from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import CodeFile, FileVersion, Project, User
from app.workspace_routes import get_membership
from app.file_schemas import FileCreate, FileResponse, FileUpdate

router = APIRouter(
    prefix="/projects",
    tags=["Files"],
)


def get_project_access(
    project_id: int,
    current_user: User,
    db: Session,
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    membership = get_membership(
        project.workspace_id,
        current_user.id,
        db,
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project access denied",
        )

    return project, membership


def build_file_response(
    code_file: CodeFile,
    db: Session,
):
    latest_version = db.execute(
        select(FileVersion)
        .where(FileVersion.file_id == code_file.id)
        .order_by(FileVersion.version_number.desc())
    ).scalars().first()

    return FileResponse(
        id=code_file.id,
        project_id=code_file.project_id,
        path=code_file.path,
        language=code_file.language,
        content=latest_version.content if latest_version else "",
        version_number=latest_version.version_number if latest_version else 0,
    )


@router.post(
    "/{project_id}/files",
    response_model=FileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_file(
    project_id: int,
    data: FileCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_project_access(project_id, current_user, db)

    existing = db.execute(
        select(CodeFile).where(
            CodeFile.project_id == project_id,
            CodeFile.path == data.path,
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="File already exists",
        )

    code_file = CodeFile(
        project_id=project_id,
        path=data.path,
        language=data.language,
    )

    db.add(code_file)
    db.flush()

    version = FileVersion(
        file_id=code_file.id,
        version_number=1,
        content=data.content,
        created_by=current_user.id,
    )

    db.add(version)
    db.commit()
    db.refresh(code_file)

    return build_file_response(code_file, db)


@router.get(
    "/{project_id}/files",
    response_model=list[FileResponse],
)
def list_files(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_project_access(project_id, current_user, db)

    files = db.execute(
        select(CodeFile)
        .where(CodeFile.project_id == project_id)
        .order_by(CodeFile.path)
    ).scalars().all()

    return [
        build_file_response(code_file, db)
        for code_file in files
    ]


@router.get(
    "/{project_id}/files/{file_id}",
    response_model=FileResponse,
)
def get_file(
    project_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_project_access(project_id, current_user, db)

    code_file = db.execute(
        select(CodeFile).where(
            CodeFile.id == file_id,
            CodeFile.project_id == project_id,
        )
    ).scalar_one_or_none()

    if code_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return build_file_response(code_file, db)


@router.put(
    "/{project_id}/files/{file_id}",
    response_model=FileResponse,
)
def update_file(
    project_id: int,
    file_id: int,
    data: FileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_project_access(project_id, current_user, db)

    code_file = db.execute(
        select(CodeFile).where(
            CodeFile.id == file_id,
            CodeFile.project_id == project_id,
        )
    ).scalar_one_or_none()

    if code_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    latest_version = db.execute(
        select(FileVersion)
        .where(FileVersion.file_id == file_id)
        .order_by(FileVersion.version_number.desc())
    ).scalars().first()

    next_version = (
        latest_version.version_number + 1
        if latest_version
        else 1
    )

    if data.path is not None:
        existing_path = db.execute(
            select(CodeFile).where(
                CodeFile.project_id == project_id,
                CodeFile.path == data.path,
                CodeFile.id != file_id,
            )
        ).scalar_one_or_none()

        if existing_path:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A file with this name already exists",
            )

        code_file.path = data.path

    if data.language is not None:
        code_file.language = data.language

    version = FileVersion(
        file_id=file_id,
        version_number=next_version,
        content=data.content,
        created_by=current_user.id,
    )

    db.add(version)
    db.commit()
    db.refresh(code_file)

    return build_file_response(code_file, db)


@router.delete(
    "/{project_id}/files/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_file(
    project_id: int,
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _, membership = get_project_access(
        project_id,
        current_user,
        db,
    )

    if membership.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Workspace admin access required",
        )

    code_file = db.execute(
        select(CodeFile).where(
            CodeFile.id == file_id,
            CodeFile.project_id == project_id,
        )
    ).scalar_one_or_none()

    if code_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    db.delete(code_file)
    db.commit()

    return None

