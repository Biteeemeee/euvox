from euvox.operation_registry.base import OperationHandler


class OperationRegistry:
    def __init__(self) -> None:
        self._handlers: dict[tuple[str, str], OperationHandler] = {}

    def register(self, handler: OperationHandler) -> None:
        key = (handler.type_name, handler.schema_version)
        self._handlers[key] = handler

    def get(self, type_name: str, schema_version: str) -> OperationHandler:
        key = (type_name, schema_version)
        handler = self._handlers.get(key)
        if handler is None:
            raise KeyError(f"No handler registered for {type_name}@{schema_version}")
        return handler

    def registered_types(self) -> list[tuple[str, str]]:
        return list(self._handlers)
