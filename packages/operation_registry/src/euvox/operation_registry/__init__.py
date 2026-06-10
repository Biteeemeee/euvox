from euvox.operation_registry.base import OperationHandler, RenderContext, RenderResult
from euvox.operation_registry.operations.create_event import CreateEventV1
from euvox.operation_registry.operations.numeric_patch import NumericPatchV1
from euvox.operation_registry.registry import OperationRegistry


def make_default_registry() -> OperationRegistry:
    registry = OperationRegistry()
    registry.register(NumericPatchV1())
    registry.register(CreateEventV1())
    return registry


DEFAULT_REGISTRY = make_default_registry()

__all__ = [
    "CreateEventV1",
    "DEFAULT_REGISTRY",
    "NumericPatchV1",
    "OperationHandler",
    "OperationRegistry",
    "RenderContext",
    "RenderResult",
    "make_default_registry",
]
