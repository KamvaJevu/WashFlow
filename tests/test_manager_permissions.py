
import pytest

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
    restore_vehicle,
)


def test_manager_can_archive_and_restore_records(db):
    # 1. Create a test business.
    business = Business(
        name="Pytest Manager Permission Business"
    )
    db.add(business)
    db.flush()

    # 2. Create a Manager user.
    user = User(
        first_name="Test",
        last_name="Manager",
        email="pytest-manager@example.com",
        password_hash="NOT_A_REAL_PASSWORD_HASH",
    )
    db.add(user)
    db.flush()

    # 3. Give the user an active Manager membership.
    membership = BusinessMembership(
        business_id=business.id,
        user_id=user.id,
        role="manager",
        status="active",
    )
    db.add(membership)
    db.flush()

    # 4. Create an active customer.
    customer = Customer(
        business_id=business.id,
        customer_type="individual",
        first_name="Manager",
        last_name="Test Customer",
    )
    db.add(customer)
    db.flush()

    # 5. Create an active vehicle.
    vehicle = Vehicle(
        business_id=business.id,
        customer_id=customer.id,
        registration_number="PYTEST-MANAGER-001",
    )
    db.add(vehicle)
    db.flush()

    # Store IDs for database verification.
    business_id = business.id
    customer_id = customer.id
    vehicle_id = vehicle.id
    membership_id = membership.id

    # Commit test setup into the outer test transaction.
    # Service-level rollbacks must not remove these records.
    db.commit()

    # 6. Manager must be able to archive customers.
    archive_customer(
        db=db,
        business_id=business_id,
        customer_id=customer_id,
        membership_id=membership_id,
        reason="Manager customer archival test.",
    )

    customer_after_archive = db.get(Customer, customer_id)
    assert customer_after_archive.is_archived is True

    # 7. Manager must be able to restore customers.
    restore_customer(
        db=db,
        business_id=business_id,
        customer_id=customer_id,
        membership_id=membership_id,
        reason="Manager customer restoration test.",
    )

    customer_after_restore = db.get(Customer, customer_id)
    assert customer_after_restore.is_archived is False

    # 8. Manager must be able to archive vehicles.
    archive_vehicle(
        db=db,
        business_id=business_id,
        vehicle_id=vehicle_id,
        membership_id=membership_id,
        reason="Manager vehicle archival test.",
    )

    vehicle_after_archive = db.get(Vehicle, vehicle_id)
    assert vehicle_after_archive.is_archived is True

    # 9. Manager must be able to restore vehicles.
    restore_vehicle(
        db=db,
        business_id=business_id,
        vehicle_id=vehicle_id,
        membership_id=membership_id,
        reason="Manager vehicle restoration test.",
    )

    vehicle_after_restore = db.get(Vehicle, vehicle_id)
    assert vehicle_after_restore.is_archived is False

    # 10. Verify all archival metadata was cleared.
    assert customer_after_restore.archive_reason is None
    assert customer_after_restore.archived_at is None

    assert vehicle_after_restore.archive_reason is None
    assert vehicle_after_restore.archived_at is None
    assert vehicle_after_restore.archive_source is None

       # 11. Verify six audit events were generated.
    audit_count = db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.business_id == business_id
        )
    )

    assert audit_count == 6
