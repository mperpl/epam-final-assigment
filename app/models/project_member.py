import enum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class GrantProjectRole(enum.Enum):
    VIEWER = "viewer"
    EDITOR = "editor"

class ProjectRole(enum.Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    OWNER = "owner"

class ProjectMember(Base):
    __tablename__ = "project_members"
    
    project_id: Mapped[UUID] = mapped_column(ForeignKey("projects.id"), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[ProjectRole] = mapped_column(Enum(ProjectRole), default=ProjectRole.VIEWER, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="members")  # type: ignore # noqa: F821
