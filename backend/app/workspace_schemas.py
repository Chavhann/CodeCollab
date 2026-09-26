from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    description: str | None
    owner_id: int


class WorkspaceMemberCreate(BaseModel):
    user_id: int
    role: str = Field(default="member", pattern="^(admin|member)$")


class WorkspaceMemberResponse(BaseModel):
    id: int
    workspace_id: int
    user_id: int
    username: str
    email: str
    role: str


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class ProjectResponse(BaseModel):
    id: int
    workspace_id: int
    name: str
    description: str | None
