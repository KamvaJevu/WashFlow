
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Customer, Vehicle
from app.services.archival_service import (
    archive_vehicle,
    archive_customer,
    restore_customer,
)


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


def test_mixed_archival_restoration():

    with SessionLocal() as db:

        # 1. Independently archive Vehicle 3.
        archive_vehicle(
            db=db,
            business_id=1,
            vehicle_id=3,
            membership_id=1,
            reason="Testing independent archival preservation.",
        )

        print("Vehicle 3 independently archived.")

        # 2. Archive Customer 2.
        # This should archive only active vehicles belonging to it.
        archive_customer(
            db=db,
            business_id=1,
            customer_id=2,
            membership_id=1,
            reason="Testing customer-driven archival.",
        )

        print("Customer 2 archived.")

        # 3. Restore Customer 2.
        # Only vehicles archived through the customer should return.
        restore_customer(
            db=db,
            business_id=1,
            customer_id=2,
            membership_id=1,
            reason="Testing selective customer restoration.",
        )

        print("Customer 2 restored.")

        # 4. Verify customer.
        customer = db.scalar(
            select(Customer).where(
                Customer.business_id == 1,
                Customer.id == 2,
            )
        )

        print("\nCustomer status:")
        print("Customer archived:", customer.is_archived)

        # 5. Verify both vehicles.
        vehicles = db.scalars(
            select(Vehicle)
            .where(
                Vehicle.business_id == 1,
                Vehicle.customer_id == 2,
            )
            .order_by(Vehicle.id)
        ).all()

        print("\nVehicle statuses:")

        for vehicle in vehicles:
            print(
                vehicle.registration_number,
                "| Archived:", vehicle.is_archived,
                "| Source:", vehicle.archive_source,
            )


if __name__ == "__main__":
    try:
        test_mixed_archival_restoration()
    finally:
        engine.dispose()
