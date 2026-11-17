
from sqlalchemy import func, select

from app.models import (
    AuditLog,
    Business,
    BusinessMembership,
    Customer,
    User,
    Vehicle,
)
from app.services.archival_service import archive_customer


def test_customer_archival_archives_active_vehicles(db):
    # 1. Create a test business.
    business = Business(
        name="Pytest Archival Business"
    )
    db.add(business)
    db.flush()

    # 2. Create an Owner user.
    user = User(
        first_name="Test",
        last_name="Owner",
        email="pytest-owner@example.com",
        password_hash="NOT_A_REAL_PASSWORD_HASH",
    )
    db.add(user)
    db.flush()

    # 3. Give the user an active Owner membership.
    membership = BusinessMembership(
        business_id=business.id,
        user_id=user.id,
        role="owner",
        status="active",
    )
    db.add(membership)
    db.flush()

    # 4. Create a customer.
    customer = Customer(
        business_id=business.id,
        customer_type="individual",
        first_name="Test",
        last_name="Customer",
    )
    db.add(customer)
    db.flush()

    # 5. Create two active vehicles for that customer.
    vehicles = [
        Vehicle(
            business_id=business.id,
            customer_id=customer.id,
            registration_number="PYTEST-001",
        ),
        Vehicle(
            business_id=business.id,
            customer_id=customer.id,
            registration_number="PYTEST-002",
        ),
    ]

    db.add_all(vehicles)
    db.flush()

    # 6. Archive the customer.
    archived_customer = archive_customer(
        db=db,
        business_id=business.id,
        customer_id=customer.id,
        membership_id=membership.id,
        reason="Customer requested account closure.",
    )

    # 7. Verify the customer was archived.
    assert archived_customer.is_archived is True
    assert archived_customer.archive_reason == (
        "Customer requested account closure."
    )

    # 8. Verify both vehicles were automatically archived.
    archived_vehicles = db.scalars(
        select(Vehicle).where(
            Vehicle.customer_id == customer.id
        )
    ).all()

    assert len(archived_vehicles) == 2

    for vehicle in archived_vehicles:
        assert vehicle.is_archived is True
        assert vehicle.archive_source == "customer"
        assert vehicle.archived_by_membership_id == membership.id

    # 9. Verify three audit events were generated.
    audit_count = db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.business_id == business.id
        )
    )

    assert audit_count == 3
