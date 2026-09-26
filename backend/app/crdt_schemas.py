from typing import Literal

from pydantic import BaseModel, Field


class CRDTOperation(BaseModel):
    type: Literal["insert", "delete"]
    position: int = Field(ge=0)
    text: str = ""
    length: int = Field(default=0, ge=0)
    operation_id: str = Field(min_length=1, max_length=100)
    client_id: str = Field(min_length=1, max_length=100)
    revision: int = Field(default=0, ge=0)
