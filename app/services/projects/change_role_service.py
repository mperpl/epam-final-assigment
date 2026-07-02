from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.database.queries.project_member import get_project_member
from app.models.project_member import ProjectRole
from app.services.utils.security import protect_owner_deletion


async def change_role_service(
    project_id: UUID,
    current_user_id: UUID,
    target_user_id: UUID,
    new_role_value: str,
    db: AsyncSession,
) -> dict:
    role_to_assign = ProjectRole(new_role_value)
    await protect_owner_deletion(current_user_id, target_user_id, project_id, db)
    member_record = await get_project_member(target_user_id, project_id, db)

    if member_record.role == role_to_assign:
        message = "User assignment role remained unchanged."
    else:
        try:
            member_record.role = role_to_assign
            await db.commit()
            message = "Member role updated successfully."
        except Exception as e:
            await db.rollback()
            raise DatabaseError(
                f"Failed to execute member privilege modification: {str(e)}"
            )

    return {
        "message": message,
        "project_id": project_id,
        "user_id": target_user_id,
        "role": member_record.role.value,
    }
