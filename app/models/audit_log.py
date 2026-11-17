from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    __table_args__ = (
        Index(
            "ix_audit_logs_business_created",
            "business_id",
            "created_at",
        ),
        Index(
            "ix_audit_logs_business_action_created",
            "business_id",
            "action_type",
            "created_at",
        ),
        Index(
            "ix_audit_logs_business_actor",
            "business_id",
            "performed_by_membership_id",
        ),
        Index(
            "ix_audit_logs_business_entity",
            "business_id",
            "entity_type",
            "entity_id",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="RESTRICT"),
        nullable=False,
    )

    performed_by_membership_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    actor_name: Mapped[str | None] = mapped_column(
        String(201),
        nullable=True,
    )

    actor_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    action_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    entity_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    entity_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    old_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    new_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )