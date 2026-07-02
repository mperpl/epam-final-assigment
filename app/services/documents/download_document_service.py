from uuid import UUID

from botocore.exceptions import ClientError
from sqlalchemy.ext.asyncio import AsyncSession
from types_aiobotocore_s3 import S3Client

from app.api.schemas.response.document import DocumentDownloadResponse
from app.aws.s3 import get_download_url_s3
from app.core.exceptions import S3StorageError
from app.database.queries.documents import get_document
from app.models.document import Document
from app.models.project_member import ProjectRole
from app.services.utils.security import user_role_in


async def download_document_service(
    project_id: UUID,
    document_id: UUID,
    user_id: UUID,
    db: AsyncSession,
    s3_client: S3Client,
) -> DocumentDownloadResponse:
    document: Document = await get_document(project_id, document_id, db)
    await user_role_in(
        project_id,
        user_id,
        (ProjectRole.OWNER, ProjectRole.EDITOR, ProjectRole.VIEWER),
        db,
    )

    try:
        url = await get_download_url_s3(document.s3_key, s3_client)
    except ClientError as e:
        raise S3StorageError(f"Failed to generate download link: {e}")
    return DocumentDownloadResponse(filename=document.filename, download_url=url)
