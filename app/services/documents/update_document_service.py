from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.database.queries.documents import get_document
from app.models.document import Document
from app.models.project_member import ProjectRole
from app.services.utils.file import update_document_filename_validator
from app.services.utils.security import user_role_in


async def update_document_service(
    project_id: UUID,
    document_id: UUID,
    new_filename: str,
    user_id: UUID,
    db: AsyncSession,
) -> Document:
    await user_role_in(project_id, user_id, (ProjectRole.OWNER, ProjectRole.EDITOR), db)

    document: Document = await get_document(project_id, document_id, db)
    old_filename = document.filename
    update_document_filename_validator(old_filename, new_filename)

    document.filename = new_filename

    try:
        await db.commit()
        await db.refresh(document)
    except Exception as e:
        await db.rollback()
        raise DatabaseError(f"Database failed to update document metadata: {e}")

    return document
