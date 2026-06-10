"""Platform-aware automation for the EU5 in-game console."""

import asyncio
import platform


class ConsoleAutomator:
    """Base protocol — send a command string to the EU5 console."""

    async def send_command(self, command: str) -> None: ...


class NullConsoleAutomator(ConsoleAutomator):
    """No-op automator used on non-Windows platforms or in tests."""

    async def send_command(self, command: str) -> None:
        pass


class WindowsConsoleAutomator(ConsoleAutomator):
    """Sends commands to the EU5 in-game console via Win32 WM_CHAR messages."""

    _TILDE = ord("~")
    _ENTER = 0x0D

    def __init__(self, window_title: str = "Europa Universalis V") -> None:
        self._title = window_title

    async def send_command(self, command: str) -> None:
        loop = asyncio.get_event_loop()
        hwnd = await loop.run_in_executor(None, self._find_window)
        if hwnd is None:
            return
        await loop.run_in_executor(None, self._post_chars, hwnd, command)

    def _find_window(self) -> int | None:
        import ctypes

        hwnd = ctypes.windll.user32.FindWindowW(None, self._title)
        return int(hwnd) if hwnd else None

    def _post_chars(self, hwnd: int, command: str) -> None:
        import ctypes
        import time

        post = ctypes.windll.user32.PostMessageW
        WM_CHAR = 0x0102
        post(hwnd, WM_CHAR, self._TILDE, 0)
        time.sleep(0.15)
        for ch in command:
            post(hwnd, WM_CHAR, ord(ch), 0)
        post(hwnd, WM_CHAR, self._ENTER, 0)
        time.sleep(0.05)
        post(hwnd, WM_CHAR, self._TILDE, 0)


def make_automator(window_title: str = "Europa Universalis V") -> ConsoleAutomator:
    """Return the appropriate automator for the current platform."""
    if platform.system() == "Windows":
        return WindowsConsoleAutomator(window_title)
    return NullConsoleAutomator()
