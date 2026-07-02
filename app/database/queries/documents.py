import os
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession

from app.aws.s3 import s3_key_generator
from app.core.exceptions import EntryNotFoundError
from app.core.settings import settings
from app.models.document import Document
from app.services.utils.file import get_file_extension_if_allowed


async def get_document(project_id: UUID, document_id: UUID, db: AsyncSession) -> Document:
    try:
        stmt = select(Document).where(and_(Document.id == document_id, Document.project_id == project_id))
        document = (await db.execute(stmt)).scalar_one_or_none()
        
        if not document:
            raise EntryNotFoundError("Document not found in this project")
        return document
    except DatabaseError as e:
        raise DatabaseError(f"Database error: {e}")
    
async def get_documents(project_id: UUID, db: AsyncSession) -> list[Document]:
    try:
        stmt = select(Document).where(Document.project_id == project_id)
        documents = (await db.execute(stmt)).scalars().all()
        
        return documents
    except DatabaseError as e:
        raise DatabaseError(f"Database error: {e}")


async def create_flush_document(project_id: UUID, filename: str, db: AsyncSession) -> Document:
    document_id = uuid4()
    original_extension = get_file_extension_if_allowed(filename)

    if original_extension in settings.ALLOWED_IMAGE_EXTENSIONS:
        final_extension = '.jpg'
        base_name, _ = os.path.splitext(filename)
        final_filename = f"{base_name}.jpg"
    else:
        final_extension = original_extension
        final_filename = filename

    final_s3_key = s3_key_generator(project_id, document_id, final_extension)

    new_document = Document(
        id=document_id,
        filename=final_filename,
        s3_key=final_s3_key,
        project_id=project_id
    )

    db.add(new_document)
    await db.flush()
    return new_document