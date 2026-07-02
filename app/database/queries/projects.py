from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntryNotFoundError
from app.models.project import Project
from app.models.project_member import ProjectMember, ProjectRole


async def create_flush_project(
    user_id: UUID, title: str, content: str, db: AsyncSession
) -> Project:
    new_project = Project(title=title, content=content, user_id=user_id)
    db.add(new_project)
    await db.flush()
    return new_project


async def get_project_if_role_in(
    user_id: UUID, project_id: UUID, roles: list[ProjectRole], db: AsyncSession
) -> Project:
    """roles=[] means any role"""
    if len(roles) == 0:
        for role in ProjectRole:
            roles.append(role)
    stmt = (
        select(Project)
        .join(ProjectMember, Project.id == ProjectMember.project_id)
        .where(
            and_(
                Project.id == project_id,
                ProjectMember.user_id == user_id,
                ProjectMember.role.in_(roles),
            )
        )
    )

    project = (await db.execute(stmt)).scalar_one_or_none()

    if not project:
        raise EntryNotFoundError(
            "Project not found or you do not have permission to edit it"
        )

    return project
