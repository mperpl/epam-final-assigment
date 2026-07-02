from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from types_aiobotocore_s3 import S3Client

from app.aws.s3 import delete_folder_s3
from app.core.exceptions import AuthorizationError, DatabaseError
from app.core.settings import settings
from app.database.queries.projects import get_project_if_role_in
from app.models.project_member import ProjectRole


async def delete_project_service(
    project_id: UUID, user_id: UUID, db: AsyncSession, s3_client: S3Client
) -> None:
    project = await get_project_if_role_in(user_id, project_id, [ProjectRole.OWNER], db)

    if not project:
        raise AuthorizationError("Only the project owner can delete this project")

    try:
        await delete_folder_s3(settings.S3_BUCKET, f"raw/{project_id}/", s3_client)
        await delete_folder_s3(
            settings.S3_BUCKET, f"projects/images/{project_id}/", s3_client
        )
        await delete_folder_s3(
            settings.S3_BUCKET, f"projects/documents/{project_id}/", s3_client
        )

        await db.delete(project)
        await db.commit()

    except (SQLAlchemyError, Exception) as e:
        await db.rollback()
        raise DatabaseError(f"Failed to delete project resources: {e}")
