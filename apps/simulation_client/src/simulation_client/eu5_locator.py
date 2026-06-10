"""Detect EU5 installation paths across Windows, macOS, and Linux."""

import platform
from pathlib import Path

_WINDOWS_STEAM_ROOTS = [
    Path("C:/Program Files (x86)/Steam/steamapps/common"),
    Path("C:/Program Files/Steam/steamapps/common"),
    Path("D:/Steam/steamapps/common"),
    Path("D:/SteamLibrary/steamapps/common"),
    Path("E:/SteamLibrary/steamapps/common"),
]

_GAME_FOLDER = "Europa Universalis V"

_MAC_STEAM_ROOT = (
    Path.home() / "Library/Application Support/Steam/steamapps/common" / _GAME_FOLDER
)
_LINUX_STEAM_ROOT = Path.home() / ".steam/steam/steamapps/common" / _GAME_FOLDER

_WINDOWS_USER_BASE = Path.home() / "Documents/Paradox Interactive" / _GAME_FOLDER
_MAC_USER_BASE = Path.home() / "Library/Application Support/Paradox Interactive" / _GAME_FOLDER
_LINUX_USER_BASE = Path.home() / ".local/share/Paradox Interactive" / _GAME_FOLDER


class Eu5Locator:
    """Finds EU5 executable and user data directories on the current platform."""

    def find_exe(self, hint: Path | None = None) -> Path | None:
        """Return the EU5 executable path, or None if not found."""
        if hint and hint.exists():
            return hint
        for candidate in self._exe_candidates():
            if candidate.exists():
                return candidate
        return None

    def find_user_dir(self, hint: Path | None = None) -> Path:
        """Return the EU5 user data directory (may not exist yet)."""
        if hint:
            return hint
        system = platform.system()
        if system == "Windows":
            return _WINDOWS_USER_BASE
        if system == "Darwin":
            return _MAC_USER_BASE
        return _LINUX_USER_BASE

    def is_eu5_available(self, exe_hint: Path | None = None) -> bool:
        return self.find_exe(exe_hint) is not None

    def _exe_candidates(self) -> list[Path]:
        system = platform.system()
        if system == "Windows":
            return [root / _GAME_FOLDER / "eu5.exe" for root in _WINDOWS_STEAM_ROOTS]
        if system == "Darwin":
            return [_MAC_STEAM_ROOT / "eu5.app/Contents/MacOS/eu5"]
        return [_LINUX_STEAM_ROOT / "eu5"]
