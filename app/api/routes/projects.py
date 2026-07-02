from uuid import UUID

from fastapi import APIRouter, status

from app.api.dependencies.auth import CURRENT_USER_ID
from app.api.schemas.dto.project import ProjectCreateDTO
from app.api.schemas.dto.project_member import ProjectRoleUpdateDTO
from app.api.schemas.dto.user import UserInviteDTO
from app.api.schemas.response.project import (
    ProjectChangeRoleResponse,
    ProjectCreateResponse,
    ProjectDeleteResponse,
    ProjectInfoResponse,
    ProjectInviteResponse,
    ProjectsGetResponse,
    ProjectUpdateResponse,
)
from app.aws.s3 import S3_CLIENT
from app.database.sql_db import DB_SESSION
from app.services.projects.change_role_service import change_role_service
from app.services.projects.create_project_service import create_project_service
from app.services.projects.delete_project_service import delete_project_service
from app.services.projects.get_accessible_projects_service import (
    get_accessible_projects_service,
)
from app.services.projects.get_project_info_service import get_project_info_service
from app.services.projects.invite_user_service import invite_user_service
from app.services.projects.remove_user_from_project_service import (
    remove_user_from_project_service,
)
from app.services.projects.update_project_service import update_project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", status_code=status.HTTP_200_OK, response_model=ProjectsGetResponse)
async def get_accessible_projects(db: DB_SESSION, user_id: CURRENT_USER_ID):
    projects = await get_accessible_projects_service(user_id, db)
    return {"projects": projects}


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=ProjectCreateResponse
)
async def create_project(
    project_data: ProjectCreateDTO, db: DB_SESSION, user_id: CURRENT_USER_ID
):
    return {
        "message": "Project created successfully.",
        "project": await create_project_service(project_data, user_id, db),
    }


@router.get(
    "/{project_id}", status_code=status.HTTP_200_OK, response_model=ProjectInfoResponse
)
async def get_project_info(project_id: UUID, db: DB_SESSION, user_id: CURRENT_USER_ID):
    return await get_project_info_service(project_id, user_id, db)


@router.put(
    "/{project_id}",
    status_code=status.HTTP_200_OK,
    response_model=ProjectUpdateResponse,
)
async def update_project_info(
    update_data: ProjectCreateDTO,
    project_id: UUID,
    db: DB_SESSION,
    user_id: CURRENT_USER_ID,
):
    return {
        "message": "Project information updated successfully.",
        "project": await update_project_service(update_data, project_id, user_id, db),
    }


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_200_OK,
    response_model=ProjectDeleteResponse,
)
async def delete_project(
    project_id: UUID, user_id: CURRENT_USER_ID, db: DB_SESSION, s3_client: S3_CLIENT
):
    await delete_project_service(project_id, user_id, db, s3_client)
    return {}


@router.post(
    "/{project_id}/user",
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectInviteResponse,
)
async def invite_user(
    project_id: UUID,
    invitee_data: UserInviteDTO,
    db: DB_SESSION,
    user_id: CURRENT_USER_ID,
):
    return await invite_user_service(project_id, user_id, invitee_data, db)


@router.put(
    "/{project_id}/user",
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectChangeRoleResponse,
)
async def change_role(
    project_id: UUID,
    target_user_id: UUID,
    role_data: ProjectRoleUpdateDTO,
    current_user: CURRENT_USER_ID,
    db: DB_SESSION,
):
    return await change_role_service(
        project_id, current_user, target_user_id, role_data.new_role.value, db
    )


@router.delete(
    "/{project_id}/user",
    status_code=status.HTTP_201_CREATED,
    response_model=ProjectChangeRoleResponse,
)
async def remove_user_from_project(
    project_id: UUID,
    target_user_id: UUID,
    current_user: CURRENT_USER_ID,
    db: DB_SESSION,
):
    return await remove_user_from_project_service(
        project_id, current_user, target_user_id, db
    )
