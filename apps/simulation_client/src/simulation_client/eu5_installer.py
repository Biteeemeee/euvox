"""Install and uninstall EU5 mods in the user data directory."""

import shutil
from pathlib import Path

_DESCRIPTOR_TEMPLATE = """\
name = "{name}"
path = "mod/{safe_name}"
tags = {{
    "Utilities"
}}
supported_version = "{game_version}"
"""


class ModInstaller:
    """Writes mod files into the EU5 user mod directory and generates a .mod descriptor."""

    def install(
        self,
        mod_files: dict[str, str],
        mod_name: str,
        user_dir: Path,
        game_version: str = "1.0.*",
    ) -> Path:
        """Install mod_files under user_dir/mod/<safe_name>/ and write the descriptor.

        Returns the mod directory path.
        """
        safe_name = _safe(mod_name)
        mod_dir = user_dir / "mod" / safe_name
        mod_dir.mkdir(parents=True, exist_ok=True)

        for rel_path, content in mod_files.items():
            dest = mod_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            # Localization files require UTF-8 BOM for EU5 to recognise them.
            encoding = "utf-8-sig" if rel_path.endswith(".yml") else "utf-8"
            dest.write_text(content, encoding=encoding)

        descriptor = user_dir / "mod" / f"{safe_name}.mod"
        descriptor.write_text(
            _DESCRIPTOR_TEMPLATE.format(
                name=mod_name,
                safe_name=safe_name,
                game_version=game_version,
            ),
            encoding="utf-8",
        )
        return mod_dir

    def uninstall(self, mod_name: str, user_dir: Path) -> None:
        """Remove the mod directory and descriptor file."""
        safe_name = _safe(mod_name)
        mod_dir = user_dir / "mod" / safe_name
        descriptor = user_dir / "mod" / f"{safe_name}.mod"
        if mod_dir.exists():
            shutil.rmtree(mod_dir)
        if descriptor.exists():
            descriptor.unlink()


def _safe(name: str) -> str:
    return name.replace(".", "_").replace(" ", "_").lower()
