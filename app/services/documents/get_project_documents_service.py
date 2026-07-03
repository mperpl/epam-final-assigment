from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.queries.documents import get_documents
from app.database.queries.project_member import get_project_member
from app.models.document import Document


async def get_project_documents_service(
    project_id: UUID, user_id: UUID, db: AsyncSession
) -> list[Document]:
    await get_project_member(user_id, project_id, db)
    return await get_documents(project_id, db)
