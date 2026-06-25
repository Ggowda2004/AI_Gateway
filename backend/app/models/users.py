from db.base import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, DateTime
from datetime import datetime, timezone


from typing import TYPE_CHECKING, List
if TYPE_CHECKING:
    from app.models.api_keys import APIKey


class User(Base):

    __tablename__ = "users"

    id:Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    email:Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    password_hash:Mapped[str] = mapped_column(
        String(128),
        nullable=False

    )

    created_at:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    api_keys:Mapped[List["APIKey"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )