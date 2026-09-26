from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crdt import CRDTDocument
from app.models import CodeFile, FileVersion


def get_latest_version(file_id: int, db: Session):
    return db.scalar(
        select(FileVersion)
        .where(FileVersion.file_id == file_id)
        .order_by(FileVersion.version_number.desc())
    )


def load_document(code_file: CodeFile, db: Session) -> CRDTDocument:
    latest = get_latest_version(code_file.id, db)

    if latest is None:
        return CRDTDocument("")

    return CRDTDocument(latest.content)


def persist_document(
    code_file: CodeFile,
    document: CRDTDocument,
    user_id: int,
    db: Session,
) -> FileVersion:
    latest = get_latest_version(code_file.id, db)

    next_version = (
        latest.version_number + 1
        if latest is not None
        else 1
    )

    version = FileVersion(
        file_id=code_file.id,
        version_number=next_version,
        content=document.content,
        created_by=user_id,
    )

    db.add(version)

    code_file.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    db.commit()
    db.refresh(version)

    return version
