from uuid import UUID

from fastapi import APIRouter, File, UploadFile, status

from app.api.dependencies.auth import CURRENT_USER_ID
from app.api.schemas.dto.document import DocumentUpdateDTO
from app.api.schemas.response.document import (
    DocumentAppendResponse,
    DocumentDeleteResponse,
    DocumentDownloadResponse,
    DocumentsGetResponse,
    DocumentUpdateResponse,
)
from app.aws.s3 import S3_CLIENT
from app.database.sql_db import DB_SESSION
from app.services.documents.append_document_service import append_document_service
from app.services.documents.delete_document_service import delete_document_service
from app.services.documents.download_document_service import download_document_service
from app.services.documents.get_project_documents_service import (
    get_project_documents_service,
)
from app.services.documents.update_document_service import update_document_service

router = APIRouter(prefix="/projects", tags=["documents"])


@router.get(
    "/{project_id}/documents",
    status_code=status.HTTP_200_OK,
    response_model=DocumentsGetResponse,
)
async def get_project_documents(project_id: UUID, db: DB_SESSION, user_id: CURRENT_USER_ID):
    return {
        "project_id": project_id,
        "documents": await get_project_documents_service(project_id, user_id, db),
    }


@router.post(
    "/{project_id}/documents",
    status_code=status.HTTP_201_CREATED,
    response_model=DocumentAppendResponse,
)
async def append_document(
    project_id: UUID,
    user_id: CURRENT_USER_ID,
    db: DB_SESSION,
    s3_client: S3_CLIENT,
    file: UploadFile = File(),
):
    new_document = await append_document_service(
        project_id, file, user_id, db, s3_client
    )
    return {
        "message": "Document successfully appended to project.",
        "document": new_document,
    }


@router.get(
    "/{project_id}/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    response_model=DocumentDownloadResponse,
)
async def download_document(
    project_id: UUID,
    document_id: UUID,
    user_id: CURRENT_USER_ID,
    db: DB_SESSION,
    s3_client: S3_CLIENT,
):
    return await download_document_service(
        project_id, document_id, user_id, db, s3_client
    )


@router.put(
    "/{project_id}/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    response_model=DocumentUpdateResponse,
)
async def update_document(
    project_id: UUID, document_id: UUID, user_id: CURRENT_USER_ID, new_filename: DocumentUpdateDTO, db: DB_SESSION
):
    return await update_document_service(project_id, document_id, new_filename.filename, user_id, db)


@router.delete(
    "/{project_id}/documents/{document_id}",
    status_code=status.HTTP_200_OK,
    response_model=DocumentDeleteResponse,
)
async def delete_document(
    project_id: UUID,
    document_id: UUID,
    user_id: CURRENT_USER_ID,
    db: DB_SESSION,
    s3_client: S3_CLIENT,
):
    await delete_document_service(project_id, document_id, user_id, db, s3_client)
    return {}
