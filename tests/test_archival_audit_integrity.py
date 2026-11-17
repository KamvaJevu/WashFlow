from datetime import datetime, timezone
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


def test_vehicle_archival_and_restoration_audit_integrity(db):
    # 1. Create a test business.
    business = Business(
        name="Pytest Audit Integrity Business"
    )
    db.add(business)
    db.flush()

    # 2. Create an Owner user.
    user = User(
        first_name="Test",
        last_name="Owner",
        email="pytest-audit-owner@example.com",
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
        first_name="Audit",
        last_name="Customer",
    )
    db.add(customer)
    db.flush()

    # 5. Create an active vehicle.
    vehicle = Vehicle(
        business_id=business.id,
        customer_id=customer.id,
        registration_number="PYTEST-AUDIT-001",
    )
    db.add(vehicle)
    db.flush()

    # Store identifiers for audit verification.
    business_id = business.id
    membership_id = membership.id
    vehicle_id = vehicle.id

    # 6. Independently archive the vehicle.
    archived_vehicle = archive_vehicle(
        db=db,
        business_id=business_id,
        vehicle_id=vehicle_id,
        membership_id=membership_id,
        reason="  Vehicle sold by the customer.  ",
    )

    # Store the archival timestamp before restoration.
    archived_at = archived_vehicle.archived_at.astimezone(
        timezone.utc
    ).isoformat()

    # 7. Restore the independently archived vehicle.
    restore_vehicle(
        db=db,
        business_id=business_id,
        vehicle_id=vehicle_id,
        membership_id=membership_id,
        reason="  Vehicle returned to service.  ",
    )

    # 8. Retrieve the audit events from the database.
    audit_events = db.scalars(
        select(AuditLog)
        .where(
            AuditLog.business_id == business_id,
            AuditLog.entity_type == "vehicle",
            AuditLog.entity_id == vehicle_id,
        )
        .order_by(AuditLog.id)
    ).all()

    assert len(audit_events) == 2

    archive_event, restore_event = audit_events

    # 9. Verify the archival audit event.
    assert archive_event.business_id == business_id
    assert archive_event.performed_by_membership_id == membership_id
    assert archive_event.actor_name == "Test Owner"
    assert archive_event.actor_email == "pytest-audit-owner@example.com"

    assert archive_event.action_type == "VEHICLE_ARCHIVED"
    assert archive_event.entity_type == "vehicle"
    assert archive_event.entity_id == vehicle_id
    assert archive_event.description == (
        "Vehicle independently archived."
    )
    assert archive_event.reason == "Vehicle sold by the customer."

    assert archive_event.old_values == {
        "is_archived": False,
        "archived_at": None,
        "archived_by_membership_id": None,
        "archive_reason": None,
        "archive_source": None,
    }

    assert archive_event.new_values == {
        "is_archived": True,
        "archived_at": archived_at,
        "archived_by_membership_id": membership_id,
        "archive_reason": "Vehicle sold by the customer.",
        "archive_source": "independent",
    }

    # Verify the archival timestamp is valid.
    assert datetime.fromisoformat(
        archive_event.new_values["archived_at"]
    )

    # 10. Verify the restoration audit event.
    assert restore_event.business_id == business_id
    assert restore_event.performed_by_membership_id == membership_id
    assert restore_event.actor_name == "Test Owner"
    assert restore_event.actor_email == "pytest-audit-owner@example.com"

    assert restore_event.action_type == "VEHICLE_RESTORED"
    assert restore_event.entity_type == "vehicle"
    assert restore_event.entity_id == vehicle_id
    assert restore_event.description == (
        "Independently archived vehicle restored."
    )
    assert restore_event.reason == "Vehicle returned to service."

    # Compare the restoration snapshot with the archival snapshot.
    # Timestamp strings may use different timezone offsets.
    assert restore_event.old_values["is_archived"] == (
        archive_event.new_values["is_archived"]
    )
    assert restore_event.old_values["archived_by_membership_id"] == (
        archive_event.new_values["archived_by_membership_id"]
    )
    assert restore_event.old_values["archive_reason"] == (
        archive_event.new_values["archive_reason"]
    )
    assert restore_event.old_values["archive_source"] == (
        archive_event.new_values["archive_source"]
    )

    assert datetime.fromisoformat(
        restore_event.old_values["archived_at"]
    ) == datetime.fromisoformat(
        archive_event.new_values["archived_at"]
    )

    assert restore_event.new_values == {
        "is_archived": False,
        "archived_at": None,
        "archived_by_membership_id": None,
        "archive_reason": None,
        "archive_source": None,
    }

    # 11. Verify both audit creation timestamps.
    for event in audit_events:
        assert event.created_at is not None
        assert event.created_at.tzinfo is not None
        assert event.created_at.utcoffset() is not None

    # 12. Verify exactly two audit events exist for this business.
    audit_count = db.scalar(
        select(func.count(AuditLog.id)).where(
            AuditLog.business_id == business_id
        )
    )

    assert audit_count == 2
