
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
    archive_vehicle,
    restore_vehicle,
)


def test_independent_vehicle_archival_and_restoration(db):
    # 1. Create a test business.
    business = Business(
        name="Pytest Vehicle Business"
    )
    db.add(business)
    db.flush()

    # 2. Create an Owner user.
    user = User(
        first_name="Test",
        last_name="Owner",
        email="pytest-vehicle-owner@example.com",
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

    # 4. Create an active customer.
    customer = Customer(
        business_id=business.id,
        customer_type="individual",
        first_name="Vehicle",
        last_name="Owner",
    )
    db.add(customer)
    db.flush()

    # 5. Create an active vehicle.
    vehicle = Vehicle(
        business_id=business.id,
        customer_id=customer.id,
        registration_number="PYTEST-VEHICLE-001",
    )
    db.add(vehicle)
    db.flush()

    # 6. Independently archive the vehicle.
    archived_vehicle = archive_vehicle(
        db=db,
        business_id=business.id,
        vehicle_id=vehicle.id,
        membership_id=membership.id,
        reason="Vehicle sold by the customer.",
    )

    # 7. Verify the vehicle was archived independently.
    assert archived_vehicle.is_archived is True
    assert archived_vehicle.archive_source == "independent"
    assert archived_vehicle.archive_reason == (
        "Vehicle sold by the customer."
    )
    assert archived_vehicle.archived_by_membership_id == membership.id
    assert archived_vehicle.archived_at is not None

    # 8. Verify the customer remains active.
    db.refresh(customer)
    assert customer.is_archived is False

    # 9. Restore the independently archived vehicle.
    restored_vehicle = restore_vehicle(
        db=db,
        business_id=business.id,
        vehicle_id=vehicle.id,
        membership_id=membership.id,
        reason="Vehicle returned to service.",
    )

    # 10. Verify all vehicle archival metadata was cleared.
    assert restored_vehicle.is_archived is False
    assert restored_vehicle.archived_at is None
    assert restored_vehicle.archived_by_membership_id is None
    assert restored_vehicle.archive_reason is None
    assert restored_vehicle.archive_source is None

    # 11. Verify the customer remains active.
    db.refresh(customer)
    assert customer.is_archived is False

    # 12. Verify two audit events were generated.
    audit_count = db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.business_id == business.id
        )
    )

    assert audit_count == 2
