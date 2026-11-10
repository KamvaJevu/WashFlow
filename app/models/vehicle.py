from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
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
            ondelete="CASCADE",
            name="fk_vehicle_customer_business",
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