from pydantic import BaseModel


class FileVersionResponse(BaseModel):
    id: int
    file_id: int
    version_number: int
    content: str
    created_by: int
