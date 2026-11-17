
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


def test_inactive_user_cannot_archive_or_restore_records(db):
    # 1. Create a test business.
    business = Business(
        name="Pytest Inactive User Business"
    )
    db.add(business)
    db.flush()

    # 2. Create an inactive Manager user.
    user = User(
        first_name="Inactive",
        last_name="User",
        email="pytest-inactive-user@example.com",
        password_hash="NOT_A_REAL_PASSWORD_HASH",
        is_active=False,
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
        first_name="Inactive",
        last_name="User Customer",
    )
    db.add(customer)
    db.flush()

    # 5. Create an active vehicle.
    vehicle = Vehicle(
        business_id=business.id,
        customer_id=customer.id,
        registration_number="PYTEST-INACTIVE-USER-001",
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

    # Expected error for an inactive user account.
    expected_error = "Your user account is not active."

    # 6. Inactive user must not archive customers.
    with pytest.raises(PermissionError, match=expected_error):
        archive_customer(
            db=db,
            business_id=business_id,
            customer_id=customer_id,
            membership_id=membership_id,
            reason="Inactive user archival attempt.",
        )

    # 7. Inactive user must not archive vehicles.
    with pytest.raises(PermissionError, match=expected_error):
        archive_vehicle(
            db=db,
            business_id=business_id,
            vehicle_id=vehicle_id,
            membership_id=membership_id,
            reason="Inactive user vehicle archival attempt.",
        )

    # 8. Inactive user must not restore customers.
    with pytest.raises(PermissionError, match=expected_error):
        restore_customer(
            db=db,
            business_id=business_id,
            customer_id=customer_id,
            membership_id=membership_id,
            reason="Inactive user restoration attempt.",
        )

    # 9. Inactive user must not restore vehicles.
    with pytest.raises(PermissionError, match=expected_error):
        restore_vehicle(
            db=db,
            business_id=business_id,
            vehicle_id=vehicle_id,
            membership_id=membership_id,
            reason="Inactive user vehicle restoration attempt.",
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
