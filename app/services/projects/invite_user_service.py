from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.dto.user import UserInviteDTO
from app.core.exceptions import (
    AuthorizationError,
    DatabaseError,
    DatabaseIntegrityError,
    EntryNotFoundError,
)
from app.database.queries.project_member import get_project_member
from app.models.project_member import ProjectMember, ProjectRole
from app.models.user import User


async def invite_user_service(
    project_id: UUID, owner_id: UUID, invitee_data: UserInviteDTO, db: AsyncSession
) -> dict:
    target_user = await _get_target_user(invitee_data, db)
    role_to_assign = ProjectRole(invitee_data.grant_role.value)
    member = await get_project_member(owner_id, project_id, db)
    if member.role != ProjectRole.OWNER:
        raise AuthorizationError("Only the project owner can invite new members.")

    try:
        new_member = ProjectMember(
            project_id=project_id, user_id=target_user.id, role=role_to_assign
        )
        db.add(new_member)
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise DatabaseIntegrityError(f"Already member: {e}")
    except Exception as e:
        await db.rollback()
        raise DatabaseError(f"Failed to record project invitation: {e}")

    return {
        "message": f"User {invitee_data.invitee_email} invited successfully.",
        "project_id": project_id,
        "invitee_email": invitee_data.invitee_email,
    }


async def _get_target_user(invitee_data: UserInviteDTO, db: AsyncSession) -> User:
    user_stmt = select(User).where(User.email == invitee_data.invitee_email)
    target_user = (await db.execute(user_stmt)).scalar_one_or_none()
    if not target_user:
        raise EntryNotFoundError(
            f"No registered user found matching email: {invitee_data.invitee_email}"
        )
    return target_user
