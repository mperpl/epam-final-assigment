from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.dto.project import ProjectCreateDTO
from app.core.exceptions import EntryNotFoundError
from app.database.queries.projects import get_project_if_role_in
from app.models.project import Project
from app.models.project_member import ProjectRole


async def update_project_service(update_data: ProjectCreateDTO, project_id: UUID, user_id: UUID, db: AsyncSession) -> Project:
    project: Project = await get_project_if_role_in(user_id, project_id, [ProjectRole.OWNER, ProjectRole.EDITOR], db)

    project.title = update_data.title
    project.content = update_data.content

    try:
        await db.commit()
        await db.refresh(project)
        return project
    except SQLAlchemyError as e:
        await db.rollback()
        raise EntryNotFoundError(f'Database could not find the entry: {e}')
        