from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
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


class Customer(Base):
    __tablename__ = "customers"

    __table_args__ = (
        CheckConstraint(
            "customer_type IN ('individual', 'company')",
            name="ck_customer_type",
        ),

        UniqueConstraint(
            "business_id",
            "id",
            name="uq_customer_business_id",
        ),
        CheckConstraint(
            """
            (
                customer_type = 'individual'
                AND first_name IS NOT NULL
                AND last_name IS NOT NULL
                AND company_name IS NULL
            )
            OR
            (
                customer_type = 'company'
                AND company_name IS NOT NULL
                AND first_name IS NULL
                AND last_name IS NULL
            )
            """,
            name="ck_customer_identity",
        ),

        CheckConstraint(
        """
        (
            is_archived = FALSE
            AND archived_at IS NULL
            AND archived_by_membership_id IS NULL
            AND archive_reason IS NULL
        )
        OR
        (
            is_archived = TRUE
            AND archived_at IS NOT NULL
            AND archived_by_membership_id IS NOT NULL
            AND archive_reason IS NOT NULL
            AND length(trim(archive_reason)) > 0
            )
            """,
            name="ck_customer_archive_consistency",
        ),

        ForeignKeyConstraint(
            ["business_id", "archived_by_membership_id"],
            ["business_memberships.business_id", "business_memberships.id"],
            ondelete="RESTRICT",
            name="fk_customer_archived_by_membership",
        ),

        Index(
            "ix_customers_business_archived",
            "business_id",
            "is_archived",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    business_id: Mapped[int] = mapped_column(
    ForeignKey("businesses.id", ondelete="RESTRICT"),
    nullable=False,
    index=True
    )

    customer_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    first_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    last_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    company_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    contact_person_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    contact_person_phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    contact_person_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
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

    business: Mapped["Business"] = relationship(
        back_populates="customers",
    )

    vehicles: Mapped[list["Vehicle"]] = relationship(
        back_populates="customer",
    )