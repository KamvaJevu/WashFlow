
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Customer, Vehicle, AuditLog
from app.services.archival_service import restore_vehicle


test_url = make_url(settings.database_url).set(
    database="washflow_test_db"
)

if test_url.database != "washflow_test_db":
    raise RuntimeError("Refusing to use a non-test database.")

engine = create_engine(test_url)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def test_vehicle_restoration():
    with SessionLocal() as db:

        vehicle = restore_vehicle(
            db=db,
            business_id=1,
            vehicle_id=3,
            membership_id=1,
            reason="Vehicle returned to the customer's active fleet.",
        )

        print("Restored vehicle:", vehicle.registration_number)
        print("Archived:", vehicle.is_archived)
        print("Archive timestamp:", vehicle.archived_at)
        print("Archive membership:", vehicle.archived_by_membership_id)
        print("Archive reason:", vehicle.archive_reason)
        print("Archive source:", vehicle.archive_source)

        customer = db.scalar(
            select(Customer).where(
                Customer.business_id == 1,
                Customer.id == 2,
            )
        )

        print("\nCustomer status:")
        print("Customer archived:", customer.is_archived)

        vehicles = db.scalars(
            select(Vehicle)
            .where(
                Vehicle.business_id == 1,
                Vehicle.customer_id == 2,
            )
            .order_by(Vehicle.id)
        ).all()

        print("\nVehicle statuses:")

        for item in vehicles:
            print(
                item.registration_number,
                "| Archived:", item.is_archived,
                "| Source:", item.archive_source,
            )

        audit_entries = db.scalars(
            select(AuditLog)
            .where(
                AuditLog.business_id == 1,
                AuditLog.entity_type == "vehicle",
                AuditLog.entity_id == 3,
            )
            .order_by(AuditLog.id)
        ).all()

        print("\nVehicle audit history:")

        for entry in audit_entries:
            print(
                entry.action_type,
                "| Entity ID:", entry.entity_id,
                "| Reason:", entry.reason,
            )

        print("\nTotal vehicle audit records:", len(audit_entries))


if __name__ == "__main__":
    try:
        test_vehicle_restoration()
    finally:
        engine.dispose()
