from typing import Protocol

from euvox.eu5_parser.types import ParsedRun


class Parser(Protocol):
    parser_version: str

    def parse(self, artifact_root_uri: str, run_manifest: dict[str, object]) -> ParsedRun:
        """Parse raw save artifacts into a normalized ParsedRun."""
        ...
