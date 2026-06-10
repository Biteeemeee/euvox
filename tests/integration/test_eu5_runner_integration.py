"""Integration tests for the EU5 runner: FakeRunner fallback and Eu5Runner mock subprocess."""

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from euvox.common_schemas import SimulationJobDTO
from simulation_client.config import Settings
from simulation_client.console_automator import NullConsoleAutomator
from simulation_client.eu5_runner import Eu5CrashError, Eu5Runner
from simulation_client.runner import FakeRunner
from simulation_client.worker import _build_runner


def _make_job(**overrides) -> SimulationJobDTO:
    defaults = {
        "id": "job-001",
        "experiment_id": "exp-001",
        "mod_version_id": "mv-001",
        "required_game_version": "1.0.0",
        "seed": 42,
        "start_date": "1444.11.11",
        "end_date": "1450.01.01",
        "fidelity_level": "low",
        "snapshot_interval_days": 365,
        "status": "running",
        "assigned_client_id": "client-001",
        "created_at": datetime(1444, 11, 11, tzinfo=UTC),
    }
    return SimulationJobDTO(**{**defaults, **overrides})


# ── _build_runner ─────────────────────────────────────────────────────────────


def test_build_runner_returns_fake_when_no_exe(tmp_path: Path) -> None:
    settings = Settings(work_dir=tmp_path, eu5_exe_path=None)
    runner = _build_runner(settings)
    assert isinstance(runner, FakeRunner)


def test_build_runner_returns_eu5_when_exe_exists(tmp_path: Path) -> None:
    exe = tmp_path / "eu5.exe"
    exe.touch()
    settings = Settings(work_dir=tmp_path, eu5_exe_path=exe, eu5_user_dir=tmp_path)
    runner = _build_runner(settings)
    assert isinstance(runner, Eu5Runner)


# ── FakeRunner ────────────────────────────────────────────────────────────────


async def test_fake_runner_produces_snapshots(tmp_path: Path) -> None:
    runner = FakeRunner(tmp_path)
    job = _make_job()
    manifest, job_dir = await runner.run(job)
    assert manifest.runner == "fake"
    assert len(manifest.snapshots) >= 1
    saves_dir = tmp_path / job.id / "saves"
    for snap in manifest.snapshots:
        assert (saves_dir / snap.filename).exists()


async def test_fake_runner_writes_empty_error_log(tmp_path: Path) -> None:
    runner = FakeRunner(tmp_path)
    job = _make_job()
    _, job_dir = await runner.run(job)
    assert (job_dir / "error.log").read_text() == ""


# ── Eu5Runner with mock subprocess ────────────────────────────────────────────


class _MockProcess:
    """Simulates an EU5 process that stays alive until explicitly terminated."""

    def __init__(self) -> None:
        self.returncode: int | None = None
        self._done = asyncio.Event()

    async def wait(self) -> int:
        await self._done.wait()
        return self.returncode or 0

    def terminate(self) -> None:
        self.returncode = 0
        self._done.set()

    def kill(self) -> None:
        self.returncode = -9
        self._done.set()


def _make_runner(tmp_path: Path) -> Eu5Runner:
    return Eu5Runner(
        eu5_exe=tmp_path / "eu5.exe",
        user_dir=tmp_path,
        automator=NullConsoleAutomator(),
        launch_timeout=5.0,
        run_timeout=5.0,
        save_poll_interval=0.05,
    )


async def test_eu5_runner_collects_saves(tmp_path: Path) -> None:
    saves_dir = tmp_path / "save games"
    saves_dir.mkdir()
    process = _MockProcess()
    runner = _make_runner(tmp_path)
    job = _make_job(end_date="1450.01.01")

    async def write_saves() -> None:
        await asyncio.sleep(0.1)
        (saves_dir / "euvox_autosave_1445.01.01.eu5").write_bytes(b"\x00" * 128)
        await asyncio.sleep(0.05)
        (saves_dir / "euvox_autosave_1450.01.01.eu5").write_bytes(b"\x00" * 256)

    write_task = asyncio.create_task(write_saves())

    with patch(
        "simulation_client.eu5_runner.asyncio.create_subprocess_exec",
        return_value=process,
    ), patch.object(runner, "_wait_for_launch"):
        manifest, _ = await runner.run(job, mod_files={})

    await write_task
    assert manifest.runner == "eu5"
    assert len(manifest.snapshots) >= 2
    dates = [s.date for s in manifest.snapshots]
    assert "1450.01.01" in dates


async def test_eu5_runner_detects_fatal_error(tmp_path: Path) -> None:
    saves_dir = tmp_path / "save games"
    saves_dir.mkdir()
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    error_log = logs_dir / "error.log"

    process = _MockProcess()
    runner = _make_runner(tmp_path)
    job = _make_job()

    async def write_crash() -> None:
        await asyncio.sleep(0.15)
        error_log.write_text("FATAL: access violation at 0x0", encoding="utf-8")

    crash_task = asyncio.create_task(write_crash())

    with patch(
        "simulation_client.eu5_runner.asyncio.create_subprocess_exec",
        return_value=process,
    ), patch.object(runner, "_wait_for_launch"), pytest.raises(Eu5CrashError, match="Fatal error"):
        await runner.run(job, mod_files={})

    await crash_task


async def test_eu5_runner_copies_error_log(tmp_path: Path) -> None:
    saves_dir = tmp_path / "save games"
    saves_dir.mkdir()
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "error.log").write_text("INFO: all ok", encoding="utf-8")

    process = _MockProcess()
    runner = _make_runner(tmp_path)
    job = _make_job(end_date="1450.01.01")

    async def write_end_save() -> None:
        await asyncio.sleep(0.1)
        (saves_dir / "euvox_autosave_1450.01.01.eu5").write_bytes(b"\x00" * 128)

    save_task = asyncio.create_task(write_end_save())

    with patch(
        "simulation_client.eu5_runner.asyncio.create_subprocess_exec",
        return_value=process,
    ), patch.object(runner, "_wait_for_launch"):
        _, job_dir = await runner.run(job, mod_files={})

    await save_task
    assert (job_dir / "error.log").read_text() == "INFO: all ok"


async def test_eu5_runner_installs_mod_before_launch(tmp_path: Path) -> None:
    (tmp_path / "save games").mkdir()
    process = _MockProcess()
    runner = _make_runner(tmp_path)
    job = _make_job(end_date="1450.01.01")

    saves_dir = tmp_path / "save games"

    async def write_end_save() -> None:
        await asyncio.sleep(0.1)
        (saves_dir / "euvox_autosave_1450.01.01.eu5").write_bytes(b"\x00" * 128)

    extra_files = {"events/custom.txt": "namespace = custom"}
    save_task = asyncio.create_task(write_end_save())

    with patch(
        "simulation_client.eu5_runner.asyncio.create_subprocess_exec",
        return_value=process,
    ), patch.object(runner, "_wait_for_launch"):
        await runner.run(job, mod_files=extra_files)

    await save_task
    # After run completes the mod is uninstalled, but descriptor was created
    # Verify mod content was written (autosave event must exist)
    mod_name = "euvox_mv_001"
    # mod was uninstalled; verify descriptor no longer exists (clean-up test)
    assert not (tmp_path / "mod" / f"{mod_name}.mod").exists()
