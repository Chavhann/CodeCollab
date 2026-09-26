from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Project, User, Workspace, WorkspaceMember
from app.workspace_schemas import (
    ProjectCreate,
    ProjectResponse,
    WorkspaceCreate,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
    WorkspaceResponse,
)

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


def get_membership(
    workspace_id: int,
    user_id: int,
    db: Session,
):
    return db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    ).scalar_one_or_none()


def require_workspace_access(
    workspace_id: int,
    current_user: User,
    db: Session,
):
    membership = get_membership(
        workspace_id,
        current_user.id,
        db,
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace access denied",
        )

    return membership


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace = Workspace(
        name=data.name,
        description=data.description,
        owner_id=current_user.id,
    )

    db.add(workspace)
    db.flush()

    owner_membership = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=current_user.id,
        role="admin",
    )

    db.add(owner_membership)
    db.commit()
    db.refresh(workspace)

    return workspace


@router.get(
    "",
    response_model=list[WorkspaceResponse],
)
def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.execute(
        select(Workspace)
        .join(
            WorkspaceMember,
            WorkspaceMember.workspace_id == Workspace.id,
        )
        .where(WorkspaceMember.user_id == current_user.id)
        .order_by(Workspace.id)
    ).scalars().all()


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    workspace_id: int,
    data: WorkspaceMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_workspace_access(
        workspace_id,
        current_user,
        db,
    )

    if membership.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace admin access required",
        )

    workspace = db.get(Workspace, workspace_id)

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    user = db.get(User, data.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    existing = get_membership(
        workspace_id,
        data.user_id,
        db,
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a workspace member",
        )

    new_membership = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=data.user_id,
        role=data.role,
    )

    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)

    return WorkspaceMemberResponse(
        id=new_membership.id,
        workspace_id=workspace_id,
        user_id=user.id,
        username=user.username,
        email=user.email,
        role=new_membership.role,
    )


@router.get(
    "/{workspace_id}/members",
    response_model=list[WorkspaceMemberResponse],
)
def list_members(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_workspace_access(
        workspace_id,
        current_user,
        db,
    )

    rows = db.execute(
        select(WorkspaceMember, User)
        .join(User, User.id == WorkspaceMember.user_id)
        .where(WorkspaceMember.workspace_id == workspace_id)
        .order_by(WorkspaceMember.id)
    ).all()

    return [
        WorkspaceMemberResponse(
            id=membership.id,
            workspace_id=membership.workspace_id,
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=membership.role,
        )
        for membership, user in rows
    ]


@router.post(
    "/{workspace_id}/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    workspace_id: int,
    data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    membership = require_workspace_access(
        workspace_id,
        current_user,
        db,
    )

    if membership.role not in ("admin", "member"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace access required",
        )

    project = Project(
        workspace_id=workspace_id,
        name=data.name,
        description=data.description,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


@router.get(
    "/{workspace_id}/projects",
    response_model=list[ProjectResponse],
)
def list_projects(
    workspace_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_workspace_access(
        workspace_id,
        current_user,
        db,
    )

    return db.execute(
        select(Project)
        .where(Project.workspace_id == workspace_id)
        .order_by(Project.id)
    ).scalars().all()
