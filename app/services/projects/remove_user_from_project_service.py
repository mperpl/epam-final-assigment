from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.database.queries.project_member import get_project_member
from app.services.utils.security import protect_owner_deletion


async def remove_user_from_project_service(
    project_id: UUID, current_user_id: UUID, target_user_id: UUID, db: AsyncSession
) -> None:
    protect_owner_deletion(current_user_id, target_user_id)
    member_record = await get_project_member(target_user_id, project_id, db)

    try:
        await db.delete(member_record)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise DatabaseError(
            f"Failed to execute member privilege modification: {str(e)}"
        )
