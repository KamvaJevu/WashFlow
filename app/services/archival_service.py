
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.business_membership import BusinessMembership
from app.models.customer import Customer
from app.models.vehicle import Vehicle
from app.services.audit_service import record_audit_event


def _validate_archival_permission(
    db: Session,
    business_id: int,
    membership_id: int,
) -> BusinessMembership:
    membership = db.scalar(
        select(BusinessMembership)
        .where(
            BusinessMembership.id == membership_id,
            BusinessMembership.business_id == business_id,
        )
        .with_for_update()
    )

    if membership is None:
        raise ValueError(
            "Active business membership not found."
        )

    if membership.status != "active":
        raise ValueError(
            "Your business membership is not active."
        )

    if not membership.user.is_active:
        raise PermissionError(
            "Your user account is not active."
        )

    if membership.role not in ("owner", "manager"):
        raise PermissionError(
            "Only Owners and Managers can archive or restore records."
        )

    return membership


def _validate_archive_reason(reason: str) -> str:
    cleaned_reason = reason.strip()

    if not cleaned_reason:
        raise ValueError(
            "An archive reason is required."
        )

    return cleaned_reason


def _validate_restoration_reason(reason: str) -> str:
    cleaned_reason = reason.strip()

    if not cleaned_reason:
        raise ValueError(
            "A restoration reason is required."
        )

    return cleaned_reason


def _get_customer(
    db: Session,
    business_id: int,
    customer_id: int,
) -> Customer:
    customer = db.scalar(
        select(Customer)
        .where(
            Customer.id == customer_id,
            Customer.business_id == business_id,
        )
        .with_for_update()
    )

    if customer is None:
        raise ValueError(
            "Customer not found in this business."
        )

    return customer


def archive_customer(
    db: Session,
    business_id: int,
    customer_id: int,
    membership_id: int,
    reason: str,
) -> Customer:
    cleaned_reason = _validate_archive_reason(reason)

    try:
        membership = _validate_archival_permission(
            db,
            business_id,
            membership_id,
        )

        customer = _get_customer(
            db,
            business_id,
            customer_id,
        )

        if customer.is_archived:
            raise ValueError(
                "Customer is already archived."
            )

        # Capture the customer's original state.
        old_customer_values = {
            "is_archived": customer.is_archived,
            "archived_at": (
                customer.archived_at.isoformat()
                if customer.archived_at else None
            ),
            "archived_by_membership_id": (
                customer.archived_by_membership_id
            ),
            "archive_reason": customer.archive_reason,
        }

        archived_at = datetime.now(timezone.utc)

        # Archive the customer.
        customer.is_archived = True
        customer.archived_at = archived_at
        customer.archived_by_membership_id = membership_id
        customer.archive_reason = cleaned_reason

        # Capture the customer's new state.
        new_customer_values = {
            "is_archived": customer.is_archived,
            "archived_at": customer.archived_at.isoformat(),
            "archived_by_membership_id": (
                customer.archived_by_membership_id
            ),
            "archive_reason": customer.archive_reason,
        }

        # Record the customer's archival event.
        user = membership.user

        record_audit_event(
            db=db,
            business_id=business_id,
            performed_by_membership_id=membership.id,
            actor_name=f"{user.first_name} {user.last_name}",
            actor_email=user.email,
            action_type="CUSTOMER_ARCHIVED",
            entity_type="customer",
            entity_id=customer.id,
            description="Customer archived.",
            reason=cleaned_reason,
            old_values=old_customer_values,
            new_values=new_customer_values,
        )

        # Find active vehicles belonging to this customer.
        vehicles = db.scalars(
            select(Vehicle)
            .where(
                Vehicle.business_id == business_id,
                Vehicle.customer_id == customer_id,
                Vehicle.is_archived.is_(False),
            )
            .with_for_update()
        ).all()

        for vehicle in vehicles:
            # Capture the vehicle's original state.
            old_vehicle_values = {
                "is_archived": vehicle.is_archived,
                "archived_at": (
                    vehicle.archived_at.isoformat()
                    if vehicle.archived_at else None
                ),
                "archived_by_membership_id": (
                    vehicle.archived_by_membership_id
                ),
                "archive_reason": vehicle.archive_reason,
                "archive_source": vehicle.archive_source,
            }

            # Archive the vehicle.
            vehicle.is_archived = True
            vehicle.archived_at = archived_at
            vehicle.archived_by_membership_id = membership_id
            vehicle.archive_reason = (
                f"Customer archived: {cleaned_reason}"
            )
            vehicle.archive_source = "customer"

            # Capture the vehicle's new state.
            new_vehicle_values = {
                "is_archived": vehicle.is_archived,
                "archived_at": vehicle.archived_at.isoformat(),
                "archived_by_membership_id": (
                    vehicle.archived_by_membership_id
                ),
                "archive_reason": vehicle.archive_reason,
                "archive_source": vehicle.archive_source,
            }

            # Record the vehicle's archival event.
            record_audit_event(
                db=db,
                business_id=business_id,
                performed_by_membership_id=membership.id,
                actor_name=f"{user.first_name} {user.last_name}",
                actor_email=user.email,
                action_type="VEHICLE_ARCHIVED",
                entity_type="vehicle",
                entity_id=vehicle.id,
                description=(
                    "Vehicle automatically archived "
                    "because its customer was archived."
                ),
                reason=cleaned_reason,
                old_values=old_vehicle_values,
                new_values=new_vehicle_values,
            )

        # Commit the customer, vehicles and audit records together.
        db.commit()

        return customer

    except Exception:
        db.rollback()
        raise


def archive_vehicle(
    db: Session,
    business_id: int,
    vehicle_id: int,
    membership_id: int,
    reason: str,
) -> Vehicle:
    cleaned_reason = _validate_archive_reason(reason)

    try:
        membership = _validate_archival_permission(
            db,
            business_id,
            membership_id,
        )

        # Identify the vehicle's customer without locking the vehicle.
        customer_id = db.scalar(
            select(Vehicle.customer_id).where(
                Vehicle.id == vehicle_id,
                Vehicle.business_id == business_id,
            )
        )

        if customer_id is None:
            raise ValueError(
                "Vehicle not found in this business."
            )

        # Lock the customer first.
        customer = _get_customer(
            db,
            business_id,
            customer_id,
        )

        if customer.is_archived:
            raise ValueError(
                "Cannot independently archive a vehicle belonging to an archived customer."
            )

        # Lock the vehicle after the customer.
        vehicle = db.scalar(
            select(Vehicle)
            .where(
                Vehicle.id == vehicle_id,
                Vehicle.business_id == business_id,
            )
            .with_for_update()
        )

        if vehicle is None:
            raise ValueError(
                "Vehicle not found in this business."
            )

        if vehicle.customer_id != customer_id:
            raise ValueError(
                "Vehicle ownership changed. Please retry the operation."
            )

        if vehicle.is_archived:
            raise ValueError(
                "Vehicle is already archived."
            )

        # Capture the vehicle's original state.
        old_vehicle_values = {
            "is_archived": vehicle.is_archived,
            "archived_at": (
                vehicle.archived_at.isoformat()
                if vehicle.archived_at else None
            ),
            "archived_by_membership_id": (
                vehicle.archived_by_membership_id
            ),
            "archive_reason": vehicle.archive_reason,
            "archive_source": vehicle.archive_source,
        }

        archived_at = datetime.now(timezone.utc)

        # Archive the vehicle.
        vehicle.is_archived = True
        vehicle.archived_at = archived_at
        vehicle.archived_by_membership_id = membership_id
        vehicle.archive_reason = cleaned_reason
        vehicle.archive_source = "independent"

        # Capture the vehicle's new state.
        new_vehicle_values = {
            "is_archived": vehicle.is_archived,
            "archived_at": vehicle.archived_at.isoformat(),
            "archived_by_membership_id": (
                vehicle.archived_by_membership_id
            ),
            "archive_reason": vehicle.archive_reason,
            "archive_source": vehicle.archive_source,
        }

        # Identify the person performing the action.
        user = membership.user

        # Record the vehicle's archival event.
        record_audit_event(
            db=db,
            business_id=business_id,
            performed_by_membership_id=membership.id,
            actor_name=f"{user.first_name} {user.last_name}",
            actor_email=user.email,
            action_type="VEHICLE_ARCHIVED",
            entity_type="vehicle",
            entity_id=vehicle.id,
            description="Vehicle independently archived.",
            reason=cleaned_reason,
            old_values=old_vehicle_values,
            new_values=new_vehicle_values,
        )

        # Commit the vehicle and audit record together.
        db.commit()

        return vehicle

    except Exception:
        db.rollback()
        raise


def restore_vehicle(
    db: Session,
    business_id: int,
    vehicle_id: int,
    membership_id: int,
    reason: str,
) -> Vehicle:
    cleaned_reason = _validate_restoration_reason(reason)

    try:
        membership = _validate_archival_permission(
            db,
            business_id,
            membership_id,
        )

        # Identify the vehicle's customer.
        customer_id = db.scalar(
            select(Vehicle.customer_id).where(
                Vehicle.id == vehicle_id,
                Vehicle.business_id == business_id,
            )
        )

        if customer_id is None:
            raise ValueError(
                "Vehicle not found in this business."
            )

        # Lock the customer first.
        customer = _get_customer(
            db,
            business_id,
            customer_id,
        )

        if customer.is_archived:
            raise ValueError(
                "Cannot independently restore a vehicle belonging to an archived customer. Restore the customer instead."
            )

        # Lock the vehicle after the customer.
        vehicle = db.scalar(
            select(Vehicle)
            .where(
                Vehicle.id == vehicle_id,
                Vehicle.business_id == business_id,
            )
            .with_for_update()
        )

        if vehicle is None:
            raise ValueError(
                "Vehicle not found in this business."
            )

        if vehicle.customer_id != customer_id:
            raise ValueError(
                "Vehicle ownership changed. Please retry the operation."
            )

        if not vehicle.is_archived:
            raise ValueError(
                "Vehicle is not archived."
            )

        if vehicle.archive_source != "independent":
            raise ValueError(
                "This vehicle was archived through its customer. Restore the customer instead."
            )

        # Capture the vehicle's original state.
        old_vehicle_values = {
            "is_archived": vehicle.is_archived,
            "archived_at": vehicle.archived_at.isoformat(),
            "archived_by_membership_id": (
                vehicle.archived_by_membership_id
            ),
            "archive_reason": vehicle.archive_reason,
            "archive_source": vehicle.archive_source,
        }

        # Restore the vehicle.
        vehicle.is_archived = False
        vehicle.archived_at = None
        vehicle.archived_by_membership_id = None
        vehicle.archive_reason = None
        vehicle.archive_source = None

        # Capture the vehicle's restored state.
        new_vehicle_values = {
            "is_archived": vehicle.is_archived,
            "archived_at": None,
            "archived_by_membership_id": None,
            "archive_reason": None,
            "archive_source": None,
        }

        user = membership.user

        # Record the restoration event.
        record_audit_event(
            db=db,
            business_id=business_id,
            performed_by_membership_id=membership.id,
            actor_name=f"{user.first_name} {user.last_name}",
            actor_email=user.email,
            action_type="VEHICLE_RESTORED",
            entity_type="vehicle",
            entity_id=vehicle.id,
            description="Independently archived vehicle restored.",
            reason=cleaned_reason,
            old_values=old_vehicle_values,
            new_values=new_vehicle_values,
        )

        # Commit restoration and audit record together.
        db.commit()

        return vehicle

    except Exception:
        db.rollback()
        raise


def restore_customer(
    db: Session,
    business_id: int,
    customer_id: int,
    membership_id: int,
    reason: str,
) -> Customer:
    cleaned_reason = _validate_restoration_reason(reason)

    try:
        membership = _validate_archival_permission(
            db,
            business_id,
            membership_id,
        )

        # Lock the customer.
        customer = _get_customer(
            db,
            business_id,
            customer_id,
        )

        if not customer.is_archived:
            raise ValueError(
                "Customer is not archived."
            )

        # Capture the customer's original state.
        old_customer_values = {
            "is_archived": customer.is_archived,
            "archived_at": customer.archived_at.isoformat(),
            "archived_by_membership_id": (
                customer.archived_by_membership_id
            ),
            "archive_reason": customer.archive_reason,
        }

        # Restore the customer.
        customer.is_archived = False
        customer.archived_at = None
        customer.archived_by_membership_id = None
        customer.archive_reason = None

        # Capture the customer's restored state.
        new_customer_values = {
            "is_archived": customer.is_archived,
            "archived_at": None,
            "archived_by_membership_id": None,
            "archive_reason": None,
        }

        user = membership.user

        # Record the customer's restoration.
        record_audit_event(
            db=db,
            business_id=business_id,
            performed_by_membership_id=membership.id,
            actor_name=f"{user.first_name} {user.last_name}",
            actor_email=user.email,
            action_type="CUSTOMER_RESTORED",
            entity_type="customer",
            entity_id=customer.id,
            description="Customer restored.",
            reason=cleaned_reason,
            old_values=old_customer_values,
            new_values=new_customer_values,
        )

        # Find only vehicles archived through this customer.
        vehicles = db.scalars(
            select(Vehicle)
            .where(
                Vehicle.business_id == business_id,
                Vehicle.customer_id == customer_id,
                Vehicle.is_archived.is_(True),
                Vehicle.archive_source == "customer",
            )
            .with_for_update()
        ).all()

        for vehicle in vehicles:
            # Capture the vehicle's original state.
            old_vehicle_values = {
                "is_archived": vehicle.is_archived,
                "archived_at": vehicle.archived_at.isoformat(),
                "archived_by_membership_id": (
                    vehicle.archived_by_membership_id
                ),
                "archive_reason": vehicle.archive_reason,
                "archive_source": vehicle.archive_source,
            }

            # Restore the vehicle.
            vehicle.is_archived = False
            vehicle.archived_at = None
            vehicle.archived_by_membership_id = None
            vehicle.archive_reason = None
            vehicle.archive_source = None

            # Capture the vehicle's restored state.
            new_vehicle_values = {
                "is_archived": vehicle.is_archived,
                "archived_at": None,
                "archived_by_membership_id": None,
                "archive_reason": None,
                "archive_source": None,
            }

            # Record the vehicle's restoration.
            record_audit_event(
                db=db,
                business_id=business_id,
                performed_by_membership_id=membership.id,
                actor_name=f"{user.first_name} {user.last_name}",
                actor_email=user.email,
                action_type="VEHICLE_RESTORED",
                entity_type="vehicle",
                entity_id=vehicle.id,
                description=(
                    "Vehicle restored because its customer "
                    "was restored."
                ),
                reason=cleaned_reason,
                old_values=old_vehicle_values,
                new_values=new_vehicle_values,
            )

        # Commit customer, vehicles and audit records together.
        db.commit()

        return customer

    except Exception:
        db.rollback()
        raise
