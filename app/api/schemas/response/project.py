from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.api.schemas.from_attributes_true import BaseResponseModel
from app.api.schemas.response.document import DocumentData
from app.models.project_member import GrantProjectRole


class ProjectBareData(BaseResponseModel):
    id: UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    user_id: UUID

class ProjectData(BaseResponseModel):
    id: UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    user_id: UUID
    documents: list[DocumentData]

class ProjectsGetResponse(BaseResponseModel):
    projects: list[ProjectBareData]

class ProjectCreateResponse(BaseResponseModel):
    message: str = "Project created successfully."
    project: ProjectData

class ProjectInfoResponse(BaseResponseModel):
    id: UUID
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    user_id: UUID
    documents: list[DocumentData]

class ProjectUpdateResponse(BaseResponseModel):
    message: str = "Project information updated successfully."
    project: ProjectBareData

class ProjectDeleteResponse(BaseModel):
    message: str = "Project and its associated documents were permanently deleted."

class ProjectInviteResponse(BaseModel):
    message: str = "Invitation sent successfully."
    project_id: UUID
    invitee_email: EmailStr

class ProjectChangeRoleResponse(BaseModel):
    message: str
    project_id: UUID
    user_id: UUID
    role: GrantProjectRole