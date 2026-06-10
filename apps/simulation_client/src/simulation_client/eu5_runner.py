"""Real EU5 runner: launches the game, installs the mod, collects saves and error log."""

import asyncio
import contextlib
import time
from pathlib import Path

import structlog
from euvox.common_schemas import SimulationJobDTO

from simulation_client.console_automator import ConsoleAutomator, make_automator
from simulation_client.eu5_installer import ModInstaller
from simulation_client.runner import RunManifest, SnapshotRecord

logger = structlog.get_logger()

# Paradox scripted-events that trigger periodic autosaves.
# The save_game effect writes to <user_dir>/save games/<path>.eu5.
_AUTOSAVE_EVENT = """\
namespace = euvox_runner

country_event = {
\tid = euvox_runner.autosave
\tis_triggered_only = yes
\thidden = yes

\toption = {
\t\tname = "euvox_runner.autosave.a"
\t\tsave_game = "euvox_autosave"
\t}
}
"""

_ON_ACTION_TEMPLATE = """\
on_actions = {{
\ton_startup = {{
\t\tcountry_event = {{
\t\t\tid = euvox_runner.autosave
\t\t\tdays = {snapshot_days}
\t\t\trepeat = yes
\t\t}}
\t}}
}}
"""

_SAVE_GLOB = "euvox_autosave*.eu5"


class Eu5LaunchError(RuntimeError): ...
class Eu5TimeoutError(RuntimeError): ...
class Eu5CrashError(RuntimeError): ...


class Eu5Runner:
    """Launches EU5, monitors saves/error.log, and returns a RunManifest."""

    def __init__(
        self,
        eu5_exe: Path,
        user_dir: Path,
        automator: ConsoleAutomator | None = None,
        launch_timeout: float = 120.0,
        run_timeout: float = 3600.0,
        save_poll_interval: float = 5.0,
    ) -> None:
        self._exe = eu5_exe
        self._user_dir = user_dir
        self._automator = automator or make_automator()
        self._launch_timeout = launch_timeout
        self._run_timeout = run_timeout
        self._save_poll_interval = save_poll_interval
        self._installer = ModInstaller()

    async def run(
        self, job: SimulationJobDTO, mod_files: dict[str, str]
    ) -> tuple[RunManifest, Path]:
        """Install the mod, launch EU5, collect saves, return (manifest, job_dir)."""
        job_dir = self._user_dir / "euvox_runs" / job.id
        saves_dir = self._user_dir / "save games"
        job_dir.mkdir(parents=True, exist_ok=True)
        saves_dir.mkdir(parents=True, exist_ok=True)

        error_log_path = self._user_dir / "logs" / "error.log"
        mod_name = f"euvox_{job.mod_version_id}"

        injected = {**mod_files, **self._autosave_files(job)}
        mod_dir = self._installer.install(
            injected, mod_name, self._user_dir, job.required_game_version
        )
        log = logger.bind(job_id=job.id, mod=mod_name)
        log.info("mod_installed", mod_dir=str(mod_dir))

        cmd = [
            str(self._exe),
            f"-mod mod/{mod_dir.name}",
            "-debug_mode",
            f"-start_date {job.start_date}",
            f"-end_date {job.end_date}",
            f"-seed {job.seed}",
            "-observe",
        ]
        log.info("launching_eu5", cmd=" ".join(cmd))
        t0 = time.monotonic()

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

        try:
            snapshots = await self._monitor(process, saves_dir, error_log_path, job, log)
        finally:
            await _terminate(process)

        elapsed = round(time.monotonic() - t0, 3)
        _copy_error_log(error_log_path, job_dir)
        self._installer.uninstall(mod_name, self._user_dir)

        return RunManifest(
            runner="eu5",
            game_version=job.required_game_version,
            seed=job.seed,
            start_date=job.start_date,
            end_date=job.end_date,
            fidelity_level=job.fidelity_level,
            elapsed_seconds=elapsed,
            snapshots=snapshots,
        ), job_dir

    async def _monitor(
        self,
        process: asyncio.subprocess.Process,
        saves_dir: Path,
        error_log: Path,
        job: SimulationJobDTO,
        log: structlog.BoundLogger,
    ) -> list[SnapshotRecord]:
        snapshots: list[SnapshotRecord] = []
        seen: set[str] = set()
        end_year = int(job.end_date.split(".")[0])
        deadline = time.monotonic() + self._run_timeout

        await self._wait_for_launch(process, log)

        while time.monotonic() < deadline:
            if process.returncode is not None and process.returncode != 0:
                reason = _read_tail(error_log)
                raise Eu5CrashError(
                    f"EU5 exited with code {process.returncode}: {reason}"
                )

            for save_file in sorted(saves_dir.glob(_SAVE_GLOB)):
                if save_file.name in seen:
                    continue
                seen.add(save_file.name)
                date = _date_from_save(save_file)
                record = SnapshotRecord(
                    date=date,
                    filename=save_file.name,
                    size_bytes=save_file.stat().st_size,
                )
                snapshots.append(record)
                log.info("snapshot", date=date, file=save_file.name)

                if date and int(date.split(".")[0]) >= end_year:
                    return snapshots

            if _has_fatal(error_log):
                raise Eu5CrashError(f"Fatal error in error.log: {_read_tail(error_log)}")

            if process.returncode == 0:
                break

            await asyncio.sleep(self._save_poll_interval)

        if time.monotonic() >= deadline:
            raise Eu5TimeoutError(f"EU5 run timed out after {self._run_timeout}s")

        return snapshots

    async def _wait_for_launch(
        self, process: asyncio.subprocess.Process, log: structlog.BoundLogger
    ) -> None:
        deadline = time.monotonic() + self._launch_timeout
        warmup = 30.0  # give the game 30 s to show the main menu before sending observe

        while time.monotonic() < deadline:
            if process.returncode is not None:
                raise Eu5LaunchError(
                    f"EU5 exited immediately with code {process.returncode}"
                )
            elapsed = time.monotonic() - (deadline - self._launch_timeout)
            if elapsed >= warmup:
                log.info("sending_observe_command")
                await self._automator.send_command("observe")
                return
            log.debug("waiting_for_launch", elapsed=round(elapsed, 1))
            await asyncio.sleep(2.0)

        raise Eu5LaunchError(f"EU5 failed to become responsive within {self._launch_timeout}s")

    def _autosave_files(self, job: SimulationJobDTO) -> dict[str, str]:
        on_action = _ON_ACTION_TEMPLATE.format(snapshot_days=job.snapshot_interval_days)
        return {
            "events/euvox_runner_autosave.txt": _AUTOSAVE_EVENT,
            "common/on_actions/euvox_runner.txt": on_action,
        }


# ── helpers ────────────────────────────────────────────────────────────────────


def _date_from_save(path: Path) -> str:
    # euvox_autosave_1450.01.01.eu5 → "1450.01.01"
    stem = path.stem
    prefix = "euvox_autosave_"
    if stem.startswith(prefix):
        return stem[len(prefix):]
    return ""


def _has_fatal(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return "FATAL" in content or "CRASH" in content
    except OSError:
        return False


def _read_tail(path: Path, chars: int = 1000) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-chars:]
    except OSError:
        return ""


def _copy_error_log(src: Path, job_dir: Path) -> None:
    if src.exists():
        with contextlib.suppress(OSError):
            (job_dir / "error.log").write_text(
                src.read_text(encoding="utf-8", errors="replace"), encoding="utf-8"
            )
    else:
        (job_dir / "error.log").write_text("", encoding="utf-8")


async def _terminate(process: asyncio.subprocess.Process) -> None:
    if process.returncode is None:
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=10.0)
        except TimeoutError:
            process.kill()
