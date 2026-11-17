
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


def test_empty_and_whitespace_reasons_are_rejected(db):
    # 1. Create a test business.
    business = Business(
        name="Pytest Reason Validation Business"
    )
    db.add(business)
    db.flush()

    # 2. Create an Owner user.
    user = User(
        first_name="Reason",
        last_name="Validation Owner",
        email="pytest-reason-owner@example.com",
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

    # 4. Create an active customer.
    customer = Customer(
        business_id=business.id,
        customer_type="individual",
        first_name="Reason",
        last_name="Validation Customer",
    )
    db.add(customer)
    db.flush()

    # 5. Create an active vehicle.
    vehicle = Vehicle(
        business_id=business.id,
        customer_id=customer.id,
        registration_number="PYTEST-REASON-001",
    )
    db.add(vehicle)
    db.flush()

    # Store IDs for database verification.
    business_id = business.id
    customer_id = customer.id
    vehicle_id = vehicle.id
    membership_id = membership.id

    # Commit setup before testing invalid reasons.
    db.commit()

    # 6. Empty and whitespace-only archival reasons must be rejected.
    with pytest.raises(
        ValueError,
        match="An archive reason is required.",
    ):
        archive_customer(
            db=db,
            business_id=business_id,
            customer_id=customer_id,
            membership_id=membership_id,
            reason="",
        )

    with pytest.raises(
        ValueError,
        match="An archive reason is required.",
    ):
        archive_vehicle(
            db=db,
            business_id=business_id,
            vehicle_id=vehicle_id,
            membership_id=membership_id,
            reason="   ",
        )


    # 7. Independently archive the vehicle with a valid reason.
    archive_vehicle(
        db=db,
        business_id=business_id,
        vehicle_id=vehicle_id,
        membership_id=membership_id,
        reason="Prepare vehicle for restoration validation.",
    )

    # 8. Archive the customer with a valid reason.
    # The independently archived vehicle must remain independently archived.
    archive_customer(
        db=db,
        business_id=business_id,
        customer_id=customer_id,
        membership_id=membership_id,
        reason="Prepare customer for restoration validation.",
    )

    # 9. Empty and whitespace-only restoration reasons must be rejected.
    with pytest.raises(
        ValueError,
        match="A restoration reason is required.",
    ):
        restore_customer(
            db=db,
            business_id=business_id,
            customer_id=customer_id,
            membership_id=membership_id,
            reason="",
        )

    with pytest.raises(
        ValueError,
        match="A restoration reason is required.",
    ):
        restore_vehicle(
            db=db,
            business_id=business_id,
            vehicle_id=vehicle_id,
            membership_id=membership_id,
            reason="   ",
        )

    # 10. Verify the customer remains archived.
    customer_after = db.get(Customer, customer_id)
    assert customer_after.is_archived is True

    # 11. Verify the vehicle remains independently archived.
    vehicle_after = db.get(Vehicle, vehicle_id)
    assert vehicle_after.is_archived is True
    assert vehicle_after.archive_source == "independent"

    # 12. Verify invalid operations generated no additional audit events.
    audit_count = db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.business_id == business_id
        )
    )

    assert audit_count == 2
