
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Customer, Vehicle, AuditLog
from app.services.archival_service import archive_customer


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


def test_customer_archival():
    with SessionLocal() as db:

        customer = archive_customer(
            db=db,
            business_id=1,
            customer_id=1,
            membership_id=1,
            reason="Customer requested removal from the active customer list.",
        )

        print("Customer archived:", customer.is_archived)

        vehicles = db.scalars(
            select(Vehicle).where(
                Vehicle.business_id == 1,
                Vehicle.customer_id == 1,
            )
        ).all()

        print("\nVehicle archival results:")

        for vehicle in vehicles:
            print(
                vehicle.registration_number,
                "| Archived:", vehicle.is_archived,
                "| Source:", vehicle.archive_source,
            )

        audit_entries = db.scalars(
            select(AuditLog)
            .where(AuditLog.business_id == 1)
            .order_by(AuditLog.id)
        ).all()

        print("\nAudit records:")

        for entry in audit_entries:
            print(
                entry.action_type,
                "|", entry.entity_type,
                "| Entity ID:", entry.entity_id,
            )

        print("\nTotal audit records:", len(audit_entries))


if __name__ == "__main__":
    try:
        test_customer_archival()
    finally:
        engine.dispose()
