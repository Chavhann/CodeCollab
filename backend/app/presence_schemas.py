from typing import Any, Literal

from pydantic import BaseModel, Field


class CursorPosition(BaseModel):
    line: int = Field(ge=0)
    column: int = Field(ge=0)


class PresenceEvent(BaseModel):
    type: Literal["presence"]
    status: Literal["online", "away", "offline"] = "online"
    cursor: CursorPosition | None = None
    selection_start: CursorPosition | None = None
    selection_end: CursorPosition | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CursorEvent(BaseModel):
    type: Literal["cursor"]
    cursor: CursorPosition
    selection_start: CursorPosition | None = None
    selection_end: CursorPosition | None = None
