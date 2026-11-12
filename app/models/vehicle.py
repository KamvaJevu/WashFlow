from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "registration_number",
            name="uq_vehicle_business_registration",
        ),
        CheckConstraint(
            "length(trim(registration_number)) > 0",
            name="ck_vehicle_registration_not_blank",
        ),
        ForeignKeyConstraint(
            ["business_id", "customer_id"],
            ["customers.business_id", "customers.id"],
            ondelete="RESTRICT",
            name="fk_vehicle_customer_business",
        ),

        CheckConstraint(
            """
        (
        is_archived = FALSE
            AND archived_at IS NULL
            AND archived_by_membership_id IS NULL
            AND archive_reason IS NULL
            AND archive_source IS NULL
        )
        OR
        (
        is_archived = TRUE
            AND archived_at IS NOT NULL
            AND archived_by_membership_id IS NOT NULL
            AND archive_reason IS NOT NULL
            AND length(trim(archive_reason)) > 0
            AND archive_source IS NOT NULL
            AND archive_source IN ('independent', 'customer')
        )
            """,
            name="ck_vehicle_archive_consistency",
        ),

    ForeignKeyConstraint(
        ["business_id", "archived_by_membership_id"],
        ["business_memberships.business_id", "business_memberships.id"],
        ondelete="RESTRICT",
        name="fk_vehicle_archived_by_membership",
        ),

    Index(
        "ix_vehicles_business_archived",
        "business_id",
        "is_archived",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    business_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    customer_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    registration_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    make: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    year: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    colour: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    archived_by_membership_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    archive_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    archive_source: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    customer: Mapped["Customer"] = relationship(
        back_populates="vehicles",
    )