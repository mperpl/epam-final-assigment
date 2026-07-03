from uuid import UUID

from botocore.exceptions import ClientError
from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from types_aiobotocore_s3 import S3Client

from app.aws.s3 import delete_file_s3, upload_file_s3
from app.core.exceptions import S3StorageError
from app.core.settings import settings
from app.database.queries.documents import create_flush_document
from app.models.document import Document
from app.models.project_member import ProjectRole
from app.services.utils.file import (
    get_content_type,
    get_file_extension_if_allowed,
    get_safe_filename,
    validate_upload_file_size,
)
from app.services.utils.security import user_role_in


async def append_document_service(
    project_id: UUID,
    file: UploadFile,
    user_id: UUID,
    db: AsyncSession,
    s3_client: S3Client,
) -> Document:
    await user_role_in(project_id, user_id, (ProjectRole.OWNER, ProjectRole.EDITOR), db)
    validate_upload_file_size(file)

    filename = get_safe_filename(file.filename)
    original_extension = get_file_extension_if_allowed(filename)
    content_type = get_content_type(filename)

    new_document: Document = await create_flush_document(project_id, filename, db)

    incoming_s3_key = f"raw/{project_id}/{new_document.id}{original_extension}"

    try:
        await upload_file_s3(
            file,
            settings.S3_BUCKET,
            incoming_s3_key,
            content_type,
            project_id,
            new_document.id,
            s3_client,
        )
    except ClientError as e:
        raise S3StorageError(f'Failed to upload file to storage: {e}')


    try:
        await db.commit()
        await db.refresh(new_document)

    except SQLAlchemyError:
        await db.rollback()
        try:
            await delete_file_s3(settings.S3_BUCKET, incoming_s3_key, s3_client)
        except Exception as e:
            raise S3StorageError(
                f"Orphaned file cleanup failed for S3 key {incoming_s3_key}: {e}"
            )

    return new_document
