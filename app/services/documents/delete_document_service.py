from uuid import UUID

from botocore.exceptions import ClientError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from types_aiobotocore_s3 import S3Client

from app.aws.s3 import delete_file_s3
from app.core.exceptions import DatabaseError, S3StorageError
from app.core.settings import settings
from app.database.queries.documents import get_document
from app.models.project_member import ProjectRole
from app.services.utils.security import user_role_in


async def delete_document_service(project_id: UUID, document_id: UUID, user_id: UUID, db: AsyncSession, s3_client: S3Client) -> None:
    await user_role_in(project_id, user_id, (ProjectRole.OWNER,), db)
    document = await get_document(project_id, document_id, db)
    s3_key = document.s3_key
    
    try:
        await db.delete(document)
        await delete_file_s3(settings.S3_BUCKET, s3_key, s3_client)
        await db.commit()
    except ClientError as e:
        raise S3StorageError(f'Cloud failed to delete the file: {e}')
    except SQLAlchemyError as e:
        await db.rollback()
        raise DatabaseError(f'Database failed to remove the document: {e}')