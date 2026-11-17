
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


def test_staff_cannot_archive_or_restore_records(db):
    # 1. Create a test business.
    business = Business(
        name="Pytest Staff Permission Business"
    )
    db.add(business)
    db.flush()

    # 2. Create a Staff user.
    user = User(
        first_name="Test",
        last_name="Staff",
        email="pytest-staff@example.com",
        password_hash="NOT_A_REAL_PASSWORD_HASH",
    )
    db.add(user)
    db.flush()

    # 3. Give the user an active Staff membership.
    membership = BusinessMembership(
        business_id=business.id,
        user_id=user.id,
        role="staff",
        status="active",
    )
    db.add(membership)
    db.flush()

    # 4. Create an active customer.
    customer = Customer(
        business_id=business.id,
        customer_type="individual",
        first_name="Staff",
        last_name="Test Customer",
    )
    db.add(customer)
    db.flush()

    # 5. Create an active vehicle.
    vehicle = Vehicle(
        business_id=business.id,
        customer_id=customer.id,
        registration_number="PYTEST-STAFF-001",
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

    # 6. Staff must not archive customers.
    with pytest.raises(PermissionError):
        archive_customer(
            db=db,
            business_id=business_id,
            customer_id=customer_id,
            membership_id=membership_id,
            reason="Staff archival attempt.",
        )

    # 7. Staff must not archive vehicles.
    with pytest.raises(PermissionError):
        archive_vehicle(
            db=db,
            business_id=business_id,
            vehicle_id=vehicle_id,
            membership_id=membership_id,
            reason="Staff vehicle archival attempt.",
        )

    # 8. Staff must not restore customers.
    with pytest.raises(PermissionError):
        restore_customer(
            db=db,
            business_id=business_id,
            customer_id=customer_id,
            membership_id=membership_id,
            reason="Staff customer restoration attempt.",
        )

    # 9. Staff must not restore vehicles.
    with pytest.raises(PermissionError):
        restore_vehicle(
            db=db,
            business_id=business_id,
            vehicle_id=vehicle_id,
            membership_id=membership_id,
            reason="Staff vehicle restoration attempt.",
        )

    # 10. Verify the customer remains active.
    customer_after = db.get(Customer, customer_id)
    assert customer_after.is_archived is False

    # 11. Verify the vehicle remains active.
    vehicle_after = db.get(Vehicle, vehicle_id)
    assert vehicle_after.is_archived is False

    # 12. Verify no audit events were generated.
    audit_count = db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.business_id == business_id
        )
    )

    assert audit_count == 0
