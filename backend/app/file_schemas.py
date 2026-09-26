from pydantic import BaseModel, Field


class FileCreate(BaseModel):
    path: str = Field(min_length=1, max_length=500)
    language: str | None = Field(default=None, max_length=50)
    path: str | None = Field(default=None, min_length=1, max_length=500)
    content: str = ""


class FileUpdate(BaseModel):
    content: str
    language: str | None = Field(default=None, max_length=50)
    path: str | None = Field(default=None, min_length=1, max_length=500)


class FileResponse(BaseModel):
    id: int
    project_id: int
    path: str
    language: str | None
    content: str
    version_number: int


