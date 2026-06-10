"""Unit tests for the EU5 runner components (no actual EU5 required)."""

import platform
from pathlib import Path

from simulation_client.console_automator import (
    NullConsoleAutomator,
    WindowsConsoleAutomator,
    make_automator,
)
from simulation_client.eu5_installer import ModInstaller, _safe
from simulation_client.eu5_locator import Eu5Locator
from simulation_client.eu5_runner import Eu5Runner, _date_from_save, _has_fatal, _read_tail

# ── Eu5Locator ────────────────────────────────────────────────────────────────


def test_locator_returns_hint_if_exists(tmp_path: Path) -> None:
    exe = tmp_path / "eu5.exe"
    exe.touch()
    locator = Eu5Locator()
    assert locator.find_exe(hint=exe) == exe


def test_locator_returns_none_if_hint_missing(tmp_path: Path) -> None:
    locator = Eu5Locator()
    assert locator.find_exe(hint=tmp_path / "nonexistent.exe") is None


def test_locator_returns_none_if_not_installed() -> None:
    # On CI / dev machines without EU5 installed, find_exe should return None.
    locator = Eu5Locator()
    assert locator.find_exe() is None


def test_locator_is_available_false_when_no_exe() -> None:
    locator = Eu5Locator()
    assert not locator.is_eu5_available()


def test_locator_is_available_true_with_hint(tmp_path: Path) -> None:
    exe = tmp_path / "eu5.exe"
    exe.touch()
    locator = Eu5Locator()
    assert locator.is_eu5_available(exe_hint=exe)


def test_locator_find_user_dir_returns_hint(tmp_path: Path) -> None:
    locator = Eu5Locator()
    assert locator.find_user_dir(hint=tmp_path) == tmp_path


def test_locator_find_user_dir_returns_platform_default() -> None:
    locator = Eu5Locator()
    result = locator.find_user_dir()
    assert result is not None
    assert "Paradox" in str(result) or "paradox" in str(result).lower()


# ── ModInstaller ──────────────────────────────────────────────────────────────


def test_install_creates_mod_dir(tmp_path: Path) -> None:
    installer = ModInstaller()
    mod_dir = installer.install(
        {"events/test.txt": "namespace = test"},
        mod_name="euvox_test",
        user_dir=tmp_path,
        game_version="1.0.*",
    )
    assert mod_dir.exists()
    assert (mod_dir / "events/test.txt").exists()


def test_install_writes_descriptor(tmp_path: Path) -> None:
    installer = ModInstaller()
    installer.install({}, "euvox_test", tmp_path, "1.0.*")
    descriptor = tmp_path / "mod" / "euvox_test.mod"
    assert descriptor.exists()
    content = descriptor.read_text()
    assert 'name = "euvox_test"' in content
    assert 'supported_version = "1.0.*"' in content


def test_install_localisation_uses_bom(tmp_path: Path) -> None:
    installer = ModInstaller()
    installer.install(
        {"localisation/english/foo_l_english.yml": "l_english:\n foo:0 \"bar\""},
        "euvox_test",
        tmp_path,
    )
    raw = (tmp_path / "mod/euvox_test/localisation/english/foo_l_english.yml").read_bytes()
    assert raw[:3] == b"\xef\xbb\xbf", "Localization file should start with UTF-8 BOM"


def test_install_txt_no_bom(tmp_path: Path) -> None:
    installer = ModInstaller()
    installer.install({"events/foo.txt": "namespace = foo"}, "euvox_test", tmp_path)
    raw = (tmp_path / "mod/euvox_test/events/foo.txt").read_bytes()
    assert raw[:3] != b"\xef\xbb\xbf"


def test_uninstall_removes_files(tmp_path: Path) -> None:
    installer = ModInstaller()
    installer.install({"events/test.txt": "namespace = test"}, "euvox_test", tmp_path)
    mod_dir = tmp_path / "mod" / "euvox_test"
    descriptor = tmp_path / "mod" / "euvox_test.mod"
    assert mod_dir.exists()
    installer.uninstall("euvox_test", tmp_path)
    assert not mod_dir.exists()
    assert not descriptor.exists()


def test_uninstall_is_idempotent(tmp_path: Path) -> None:
    installer = ModInstaller()
    installer.uninstall("nonexistent_mod", tmp_path)  # must not raise


def test_safe_name_sanitizes_dots_and_spaces() -> None:
    assert _safe("euvox.test mod") == "euvox_test_mod"


# ── ConsoleAutomator ──────────────────────────────────────────────────────────


def test_make_automator_returns_null_on_non_windows() -> None:
    if platform.system() != "Windows":
        assert isinstance(make_automator(), NullConsoleAutomator)


async def test_null_automator_send_command_is_awaitable() -> None:
    automator = NullConsoleAutomator()
    await automator.send_command("observe")


def test_windows_automator_has_correct_title() -> None:
    auto = WindowsConsoleAutomator("EU5 Custom Title")
    assert auto._title == "EU5 Custom Title"


# ── Eu5Runner helpers ─────────────────────────────────────────────────────────


def test_date_from_save_parses_date() -> None:
    p = Path("euvox_autosave_1450.01.01.eu5")
    assert _date_from_save(p) == "1450.01.01"


def test_date_from_save_unknown_format() -> None:
    p = Path("something_else.eu5")
    assert _date_from_save(p) == ""


def test_has_fatal_true_when_crash_in_log(tmp_path: Path) -> None:
    log = tmp_path / "error.log"
    log.write_text("FATAL: access violation at 0x000", encoding="utf-8")
    assert _has_fatal(log)


def test_has_fatal_false_when_clean_log(tmp_path: Path) -> None:
    log = tmp_path / "error.log"
    log.write_text("INFO: game started normally", encoding="utf-8")
    assert not _has_fatal(log)


def test_has_fatal_false_when_missing(tmp_path: Path) -> None:
    assert not _has_fatal(tmp_path / "missing.log")


def test_read_tail_returns_last_n_chars(tmp_path: Path) -> None:
    log = tmp_path / "error.log"
    log.write_text("a" * 2000, encoding="utf-8")
    tail = _read_tail(log, chars=100)
    assert len(tail) == 100


def test_read_tail_returns_empty_when_missing(tmp_path: Path) -> None:
    assert _read_tail(tmp_path / "missing.log") == ""


# ── Eu5Runner autosave_files ──────────────────────────────────────────────────


def _make_job(snapshot_interval_days: int = 365) -> object:
    from unittest.mock import MagicMock

    job = MagicMock()
    job.snapshot_interval_days = snapshot_interval_days
    return job


def test_autosave_files_contain_both_entries(tmp_path: Path) -> None:
    runner = Eu5Runner(
        eu5_exe=tmp_path / "eu5.exe",
        user_dir=tmp_path,
        automator=NullConsoleAutomator(),
    )
    files = runner._autosave_files(_make_job(365))
    assert "events/euvox_runner_autosave.txt" in files
    assert "common/on_actions/euvox_runner.txt" in files


def test_autosave_on_action_uses_snapshot_interval(tmp_path: Path) -> None:
    runner = Eu5Runner(
        eu5_exe=tmp_path / "eu5.exe",
        user_dir=tmp_path,
        automator=NullConsoleAutomator(),
    )
    files = runner._autosave_files(_make_job(730))
    assert "730" in files["common/on_actions/euvox_runner.txt"]


def test_autosave_event_has_save_game_effect(tmp_path: Path) -> None:
    runner = Eu5Runner(
        eu5_exe=tmp_path / "eu5.exe",
        user_dir=tmp_path,
        automator=NullConsoleAutomator(),
    )
    event_txt = runner._autosave_files(_make_job())["events/euvox_runner_autosave.txt"]
    assert "save_game" in event_txt
    assert "euvox_runner.autosave" in event_txt
