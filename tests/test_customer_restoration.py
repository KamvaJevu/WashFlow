
from sqlalchemy import func, select

from app.models import (
    AuditLog,
    Business,
    BusinessMembership,
    Customer,
    User,
    Vehicle,
)
from app.services.archival_service import (
    archive_customer,
    archive_vehicle,
    restore_customer,
)


def test_customer_restoration_preserves_independently_archived_vehicles(db):
    # 1. Create a test business.
    business = Business(
        name="Pytest Restoration Business"
    )
    db.add(business)
    db.flush()

    # 2. Create an Owner user.
    user = User(
        first_name="Test",
        last_name="Owner",
        email="pytest-restoration-owner@example.com",
        password_hash="NOT_A_REAL_PASSWORD_HASH",
    )
    db.add(user)
    db.flush()

    # 3. Create an active Owner membership.
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
        first_name="Restoration",
        last_name="Customer",
    )
    db.add(customer)
    db.flush()

    # 5. Create two active vehicles.
    independent_vehicle = Vehicle(
        business_id=business.id,
        customer_id=customer.id,
        registration_number="PYTEST-RESTORE-001",
    )

    customer_vehicle = Vehicle(
        business_id=business.id,
        customer_id=customer.id,
        registration_number="PYTEST-RESTORE-002",
    )

    db.add_all([
        independent_vehicle,
        customer_vehicle,
    ])
    db.flush()

    # 6. Independently archive the first vehicle.
    archive_vehicle(
        db=db,
        business_id=business.id,
        vehicle_id=independent_vehicle.id,
        membership_id=membership.id,
        reason="Vehicle independently archived for testing.",
    )

    # 7. Archive the customer.
    archive_customer(
        db=db,
        business_id=business.id,
        customer_id=customer.id,
        membership_id=membership.id,
        reason="Customer archived for restoration testing.",
    )

    # 8. Restore the customer.
    restored_customer = restore_customer(
        db=db,
        business_id=business.id,
        customer_id=customer.id,
        membership_id=membership.id,
        reason="Customer is returning to active service.",
    )

    # 9. Verify the customer was restored.
    assert restored_customer.is_archived is False
    assert restored_customer.archived_at is None
    assert restored_customer.archived_by_membership_id is None
    assert restored_customer.archive_reason is None

    # 10. Reload both vehicles from the database.
    db.refresh(independent_vehicle)
    db.refresh(customer_vehicle)

    # 11. The independently archived vehicle must remain archived.
    assert independent_vehicle.is_archived is True
    assert independent_vehicle.archive_source == "independent"
    assert independent_vehicle.archive_reason == (
        "Vehicle independently archived for testing."
    )

    # 12. The vehicle archived through the customer must be restored.
    assert customer_vehicle.is_archived is False
    assert customer_vehicle.archived_at is None
    assert customer_vehicle.archived_by_membership_id is None
    assert customer_vehicle.archive_reason is None
    assert customer_vehicle.archive_source is None

    # 13. Verify five audit events.
    audit_count = db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.business_id == business.id
        )
    )

    assert audit_count == 5
