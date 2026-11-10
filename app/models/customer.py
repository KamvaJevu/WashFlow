
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
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
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    business_id: Mapped[int] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
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
