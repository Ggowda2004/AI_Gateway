from db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, String, Integer, Float, DateTime
from datetime import datetime, timezone

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.api_keys import APIKey
    from app.models.users import User


class AuditLogs(Base):

    __tablename__ = "audit_logs"

    id:Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    user_id:Mapped[uuid.UUID]=mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id",ondelete="SET NULL"),
        nullable=True
    )

    api_key_id:Mapped[uuid.UUID]=mapped_column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id",ondelete="SET NULL"),
        nullable=True
    )

    provider:Mapped[str] = mapped_column(
        String
    )

    model:Mapped[str] = mapped_column(
        String
    )

    latency:Mapped[int] = mapped_column(
        Integer
    )

    prompt_tokens:Mapped[int] = mapped_column(
        Integer
    )

    total_tokens:Mapped[int] = mapped_column(
        Integer
    )

    estimated_cost:Mapped[float] = mapped_column(
        Float
    )
    
    status:Mapped[str] = mapped_column(
        String
    )

    created_at:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    user:Mapped["User"]=relationship(
        back_populates="audit_logs"
    )

    api_key:Mapped["APIKey"]=relationship(
        back_populates="audit_logs"
    )