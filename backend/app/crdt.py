from dataclasses import dataclass


@dataclass(frozen=True)
class OperationResult:
    content: str
    revision: int


class CRDTDocument:
    def __init__(self, content: str = ""):
        self.content = content
        self.revision = 0
        self.applied_operations: set[str] = set()

    def apply_insert(
        self,
        position: int,
        text: str,
        operation_id: str,
    ) -> OperationResult:
        if operation_id in self.applied_operations:
            return OperationResult(
                content=self.content,
                revision=self.revision,
            )

        position = max(0, min(position, len(self.content)))

        self.content = (
            self.content[:position]
            + text
            + self.content[position:]
        )

        self.revision += 1
        self.applied_operations.add(operation_id)

        return OperationResult(
            content=self.content,
            revision=self.revision,
        )

    def apply_delete(
        self,
        position: int,
        length: int,
        operation_id: str,
    ) -> OperationResult:
        if operation_id in self.applied_operations:
            return OperationResult(
                content=self.content,
                revision=self.revision,
            )

        if position < 0:
            position = 0

        if position > len(self.content):
            position = len(self.content)

        length = max(0, length)

        end = min(
            position + length,
            len(self.content),
        )

        self.content = (
            self.content[:position]
            + self.content[end:]
        )

        self.revision += 1
        self.applied_operations.add(operation_id)

        return OperationResult(
            content=self.content,
            revision=self.revision,
        )

    def apply_operation(self, operation):
        if operation.type == "insert":
            return self.apply_insert(
                position=operation.position,
                text=operation.text,
                operation_id=operation.operation_id,
            )

        if operation.type == "delete":
            return self.apply_delete(
                position=operation.position,
                length=operation.length,
                operation_id=operation.operation_id,
            )

        raise ValueError(
            f"Unsupported operation type: {operation.type}"
        )

    def snapshot(self) -> OperationResult:
        return OperationResult(
            content=self.content,
            revision=self.revision,
        )
