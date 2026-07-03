from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.dto.project import ProjectCreateDTO
from app.core.exceptions import DatabaseIntegrityError
from app.database.queries.project_member import create_flush_project_member
from app.database.queries.projects import create_flush_project
from app.models.project import Project
from app.models.project_member import ProjectRole


async def create_project_service(
    project_data: ProjectCreateDTO, user_id: UUID, db: AsyncSession
) -> Project:
    try:
        async with db.begin():
            new_project = await create_flush_project(
                user_id, project_data.title, project_data.content, db
            )
            await create_flush_project_member(
                user_id, new_project.id, ProjectRole.OWNER, db
            )
            await db.refresh(new_project)
    except IntegrityError as e:
        raise DatabaseIntegrityError(f'Database integrity error: {e}')


    return new_project
