import importlib

import pytest

PACKAGES = [
    "euvox.core",
    "euvox.common_schemas",
    "euvox.operation_registry",
    "euvox.search_space",
    "euvox.mod_rendering",
    "euvox.eu5_parser",
    "euvox.metrics",
    "euvox.client_protocol",
    "euvox.artifact_store",
]


@pytest.mark.parametrize("module", PACKAGES)
def test_package_importable(module: str) -> None:
    importlib.import_module(module)
