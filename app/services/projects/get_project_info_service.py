from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import EntryNotFoundError
from app.models.project import Project
from app.models.project_member import ProjectMember


async def get_project_info_service(project_id: UUID, user_id: UUID, db: AsyncSession) -> Project:
    stmt = (
        select(Project)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .where(
            and_(Project.id == project_id,
                ProjectMember.user_id == user_id))
        .options(selectinload(Project.documents))
    )
    
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise EntryNotFoundError("Project not found or access denied.")
        
    return project