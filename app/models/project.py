from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(Uuid, default=uuid4, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="projects")  # type: ignore # noqa: F821
    documents: Mapped[list["Document"]] = relationship( # type: ignore # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )  
    members: Mapped[list["ProjectMember"]] = relationship( # type: ignore # noqa: F821
        back_populates="project", cascade="all, delete-orphan"
    )  
