from pydantic import BaseModel

from app.models.project_member import GrantProjectRole


class ProjectRoleUpdateDTO(BaseModel):
    new_role: GrantProjectRole
