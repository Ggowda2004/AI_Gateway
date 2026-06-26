from db.base import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey, String, DateTime, Boolean
from datetime import datetime, timezone


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.users import User

class APIKey(Base):

    __tablename__ = "api_keys"

    id:Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id:Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    key_hash:Mapped[str]=mapped_column(
        String(128),
        nullable=False
    )

    key_id:Mapped[str]= mapped_column(
        String(16),
        nullable=False,
        index=True,
        unique=True
    ) 

    name:Mapped[str] = mapped_column(
        String(128),
    )

    is_active:Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at:Mapped[datetime]=mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )


    user:Mapped["User"] = relationship(
        back_populates="api_keys"
    )