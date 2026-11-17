
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


def test_manager_cannot_access_another_business_records(db):
    # 1. Create Business A (Manager's business).
    business_a = Business(
        name="Pytest Cross Business A"
    )
    db.add(business_a)
    db.flush()

    # 2. Create Business B (owns the protected records).
    business_b = Business(
        name="Pytest Cross Business B"
    )
    db.add(business_b)
    db.flush()

    # 3. Create a Manager user for Business A.
    user = User(
        first_name="Cross",
        last_name="Business Manager",
        email="pytest-cross-business@example.com",
        password_hash="NOT_A_REAL_PASSWORD_HASH",
    )
    db.add(user)
    db.flush()

    # 4. Give the user an active Manager membership in Business A only.
    membership = BusinessMembership(
        business_id=business_a.id,
        user_id=user.id,
        role="manager",
        status="active",
    )
    db.add(membership)
    db.flush()

    # 5. Create an active customer belonging to Business B.
    customer = Customer(
        business_id=business_b.id,
        customer_type="individual",
        first_name="Protected",
        last_name="Customer",
    )
    db.add(customer)
    db.flush()

    # 6. Create an active vehicle belonging to Business B.
    vehicle = Vehicle(
        business_id=business_b.id,
        customer_id=customer.id,
        registration_number="PYTEST-CROSS-BUSINESS-001",
    )
    db.add(vehicle)
    db.flush()

    # Store IDs for database verification.
    business_b_id = business_b.id
    customer_id = customer.id
    vehicle_id = vehicle.id
    membership_id = membership.id

    # Commit setup so service-level rollbacks cannot remove it.
    db.commit()

    # Expected error when membership does not belong to the target business.
    expected_error = "Active business membership not found."

    # 7. Manager must not archive Business B's customer.
    with pytest.raises(ValueError, match=expected_error):
        archive_customer(
            db=db,
            business_id=business_b_id,
            customer_id=customer_id,
            membership_id=membership_id,
            reason="Cross-business customer archival attempt.",
        )

    # 8. Manager must not archive Business B's vehicle.
    with pytest.raises(ValueError, match=expected_error):
        archive_vehicle(
            db=db,
            business_id=business_b_id,
            vehicle_id=vehicle_id,
            membership_id=membership_id,
            reason="Cross-business vehicle archival attempt.",
        )

    # 9. Manager must not restore Business B's customer.
    with pytest.raises(ValueError, match=expected_error):
        restore_customer(
            db=db,
            business_id=business_b_id,
            customer_id=customer_id,
            membership_id=membership_id,
            reason="Cross-business customer restoration attempt.",
        )

    # 10. Manager must not restore Business B's vehicle.
    with pytest.raises(ValueError, match=expected_error):
        restore_vehicle(
            db=db,
            business_id=business_b_id,
            vehicle_id=vehicle_id,
            membership_id=membership_id,
            reason="Cross-business vehicle restoration attempt.",
        )

    # 11. Verify Business B's customer remains active.
    customer_after = db.get(Customer, customer_id)
    assert customer_after.is_archived is False

    # 12. Verify Business B's vehicle remains active.
    vehicle_after = db.get(Vehicle, vehicle_id)
    assert vehicle_after.is_archived is False

    # 13. Verify no audit events were generated for Business B.
    audit_count = db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.business_id == business_b_id
        )
    )

    assert audit_count == 0

def test_manager_cannot_access_foreign_records_using_own_business_id(db):
    # 1. Create Business A (Manager's business).
    business_a = Business(
        name="Pytest Foreign Record Business A"
    )
    db.add(business_a)
    db.flush()

    # 2. Create Business B (owns the protected records).
    business_b = Business(
        name="Pytest Foreign Record Business B"
    )
    db.add(business_b)
    db.flush()

    # 3. Create a Manager user for Business A.
    user = User(
        first_name="Foreign",
        last_name="Record Manager",
        email="pytest-foreign-record@example.com",
        password_hash="NOT_A_REAL_PASSWORD_HASH",
    )
    db.add(user)
    db.flush()

    # 4. Give the user an active Manager membership in Business A.
    membership = BusinessMembership(
        business_id=business_a.id,
        user_id=user.id,
        role="manager",
        status="active",
    )
    db.add(membership)
    db.flush()

    # 5. Create an active customer belonging to Business B.
    customer = Customer(
        business_id=business_b.id,
        customer_type="individual",
        first_name="Protected",
        last_name="Foreign Customer",
    )
    db.add(customer)
    db.flush()

    # 6. Create an active vehicle belonging to Business B.
    vehicle = Vehicle(
        business_id=business_b.id,
        customer_id=customer.id,
        registration_number="PYTEST-FOREIGN-RECORD-001",
    )
    db.add(vehicle)
    db.flush()

    # Store IDs for database verification.
    business_a_id = business_a.id
    customer_id = customer.id
    vehicle_id = vehicle.id
    membership_id = membership.id

    # Commit setup before testing rejected operations.
    db.commit()

    # Expected errors when records do not belong to Business A.
    expected_customer_error = "Customer not found in this business."
    expected_vehicle_error = "Vehicle not found in this business."

    # 7. Manager must not archive the foreign customer.
    with pytest.raises(ValueError, match=expected_customer_error):
        archive_customer(
            db=db,
            business_id=business_a_id,
            customer_id=customer_id,
            membership_id=membership_id,
            reason="Foreign customer archival attempt.",
        )

    # 8. Manager must not archive the foreign vehicle.
    with pytest.raises(ValueError, match=expected_vehicle_error):
        archive_vehicle(
            db=db,
            business_id=business_a_id,
            vehicle_id=vehicle_id,
            membership_id=membership_id,
            reason="Foreign vehicle archival attempt.",
        )

    # 9. Manager must not restore the foreign customer.
    with pytest.raises(ValueError, match=expected_customer_error):
        restore_customer(
            db=db,
            business_id=business_a_id,
            customer_id=customer_id,
            membership_id=membership_id,
            reason="Foreign customer restoration attempt.",
        )

    # 10. Manager must not restore the foreign vehicle.
    with pytest.raises(ValueError, match=expected_vehicle_error):
        restore_vehicle(
            db=db,
            business_id=business_a_id,
            vehicle_id=vehicle_id,
            membership_id=membership_id,
            reason="Foreign vehicle restoration attempt.",
        )

    # 11. Verify the foreign customer remains active.
    customer_after = db.get(Customer, customer_id)
    assert customer_after.is_archived is False

    # 12. Verify the foreign vehicle remains active.
    vehicle_after = db.get(Vehicle, vehicle_id)
    assert vehicle_after.is_archived is False

    # 13. Verify no audit events were generated for either business.
    audit_count = db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.business_id.in_(
                [business_a_id, business_b.id]
            )
        )
    )

    assert audit_count == 0
