from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import Project
from app.models.project_member import ProjectMember


async def get_accessible_projects_service(user_id: UUID, db: AsyncSession) -> list[Project]:
    stmt = (
        select(Project)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .where(ProjectMember.user_id == user_id)
        .options(selectinload(Project.documents))
    )
    
    projects = (await db.execute(stmt)).scalars().all()
    return projects