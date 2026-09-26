from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import FileVersion, CodeFile, User
from app.file_routes import get_project_access
from app.version_schemas import FileVersionResponse

router = APIRouter(
    prefix="/projects",
    tags=["Version History"],
)


@router.get(
    "/{project_id}/files/{file_id}/versions",
    response_model=list[FileVersionResponse],
)
def list_file_versions(
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

    versions = db.execute(
        select(FileVersion)
        .where(FileVersion.file_id == file_id)
        .order_by(FileVersion.version_number.asc())
    ).scalars().all()

    return versions
