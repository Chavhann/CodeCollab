from typing import Any

from pydantic import BaseModel, Field


class CollaborationEvent(BaseModel):
    type: str = Field(min_length=1, max_length=50)
    payload: dict[str, Any] = Field(default_factory=dict)
