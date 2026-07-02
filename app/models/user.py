from uuid import UUID, uuid4

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid, default=uuid4, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    projects: Mapped[list["Project"]] = relationship(  # type: ignore # noqa: F821
        back_populates="owner", cascade="all, delete-orphan"
    )  
