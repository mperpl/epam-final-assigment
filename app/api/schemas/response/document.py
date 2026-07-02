from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.api.schemas.from_attributes_true import BaseResponseModel


class DocumentData(BaseResponseModel):
    id: UUID
    filename: str
    added_at: datetime
    project_id: UUID


class DocumentsGetResponse(BaseResponseModel):
    project_id: UUID
    documents: list[DocumentData]


class DocumentAppendResponse(BaseResponseModel):
    document: DocumentData
    message: str = "Document successfully appended to project."


class DocumentDownloadResponse(BaseResponseModel):
    filename: str
    download_url: str


class DocumentUpdateResponse(BaseResponseModel):
    message: str = "Document metadata updated successfully."
    document: DocumentData


class DocumentDeleteResponse(BaseModel):
    message: str = "Document successfully removed from storage."
