from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.queries.documents import get_documents
from app.models.document import Document


async def get_project_documents_service(
    project_id: UUID, db: AsyncSession
) -> list[Document]:
    return await get_documents(project_id, db)
