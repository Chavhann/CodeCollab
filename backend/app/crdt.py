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
        self.insert_operations: list[dict] = []

    def apply_insert(
        self,
        position: int,
        text: str,
        operation_id: str,
        revision: int = 0,
    ) -> OperationResult:
        if operation_id in self.applied_operations:
            return OperationResult(
                content=self.content,
                revision=self.revision,
            )

        original_position = position
        position = max(0, min(position, len(self.content)))

        if revision < self.revision:
            for operation in self.insert_operations:
                if operation["revision"] >= revision:
                    if operation["original_position"] < original_position:
                        position += len(operation["text"])
                    elif (
                        operation["original_position"] == original_position
                        and operation["operation_id"] < operation_id
                    ):
                        position += len(operation["text"])

        self.content = (
            self.content[:position]
            + text
            + self.content[position:]
        )

        self.revision += 1
        self.applied_operations.add(operation_id)
        self.insert_operations.append(
            {
                "revision": revision,
                "original_position": original_position,
                "position": position,
                "operation_id": operation_id,
                "text": text,
            }
        )

        return OperationResult(
            content=self.content,
            revision=self.revision,
        )

    def apply_delete(
        self,
        position: int,
        length: int,
        operation_id: str,
        revision: int = 0,
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
                revision=operation.revision,
            )

        if operation.type == "delete":
            return self.apply_delete(
                position=operation.position,
                length=operation.length,
                operation_id=operation.operation_id,
                revision=operation.revision,
            )

        raise ValueError(
            f"Unsupported operation type: {operation.type}"
        )

    def snapshot(self) -> OperationResult:
        return OperationResult(
            content=self.content,
            revision=self.revision,
        )
