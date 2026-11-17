
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Customer, Vehicle
from app.services.archival_service import (
    archive_customer,
    archive_vehicle,
    restore_customer,
    restore_vehicle,
)


test_url = make_url(settings.database_url).set(
    database="washflow_test_db"
)

if test_url.database != "washflow_test_db":
    raise RuntimeError("Refusing to use a non-test database.")

engine = create_engine(test_url)


def attempt_staff_action(db, action_name, action):

    try:
        action()
    except PermissionError as exc:
        print(f"{action_name}: BLOCKED CORRECTLY")
        print("Reason:", exc)
    else:
        raise AssertionError(
            f"{action_name} unexpectedly succeeded."
        )


def test_staff_permissions():

    with Session(engine) as db:

        # Verify the test records exist.
        customer = db.scalar(
            select(Customer).where(
                Customer.business_id == 1,
                Customer.id == 2,
            )
        )

        vehicle = db.scalar(
            select(Vehicle).where(
                Vehicle.business_id == 1,
                Vehicle.id == 3,
            )
        )

        if customer is None or vehicle is None:
            raise RuntimeError("Required test records not found.")

        # Staff membership ID 2 attempts all four operations.
        attempt_staff_action(
            db,
            "Archive customer",
            lambda: archive_customer(
                db=db,
                business_id=1,
                customer_id=2,
                membership_id=2,
                reason="Staff permission test.",
            ),
        )

        attempt_staff_action(
            db,
            "Archive vehicle",
            lambda: archive_vehicle(
                db=db,
                business_id=1,
                vehicle_id=3,
                membership_id=2,
                reason="Staff permission test.",
            ),
        )

        attempt_staff_action(
            db,
            "Restore customer",
            lambda: restore_customer(
                db=db,
                business_id=1,
                customer_id=2,
                membership_id=2,
                reason="Staff permission test.",
            ),
        )

        attempt_staff_action(
            db,
            "Restore vehicle",
            lambda: restore_vehicle(
                db=db,
                business_id=1,
                vehicle_id=3,
                membership_id=2,
                reason="Staff permission test.",
            ),
        )

        print("\nAll four Staff permission checks passed.")


if __name__ == "__main__":
    try:
        test_staff_permissions()
    finally:
        engine.dispose()
