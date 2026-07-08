from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntryNotFoundError
from app.models.project_member import ProjectMember, ProjectRole


async def create_flush_project_member(
    user_id: UUID, project_id: UUID, role: ProjectRole, db: AsyncSession
) -> ProjectMember:
    project_member = ProjectMember(project_id=project_id, user_id=user_id, role=role)
    db.add(project_member)
    await db.flush()

    return project_member


async def get_project_member(
    user_id: UUID, project_id: UUID, db: AsyncSession
) -> ProjectMember:
    stmt = select(ProjectMember).where(
        and_(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )

    member_record = (await db.execute(stmt)).scalar_one_or_none()
    if not member_record:
        raise EntryNotFoundError(
            "Target user is not currently a member of this project."
        )
    return member_record
