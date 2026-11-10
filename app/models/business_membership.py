
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class BusinessMembership(Base):
    __tablename__ = "business_memberships"

    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "user_id",
            name="uq_business_user_membership",
        ),
        CheckConstraint(
            "role IN ('owner', 'manager', 'staff')",
            name="ck_membership_role",
        ),
        CheckConstraint(
            "status IN ('invited', 'active', 'suspended')",
            name="ck_membership_status",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="invited",
        nullable=False
    )

    joined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    business: Mapped["Business"] = relationship(
        back_populates="memberships"
    )

    user: Mapped["User"] = relationship(
        back_populates="memberships"
    )