
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Customer, Vehicle


test_url = make_url(settings.database_url).set(
    database="washflow_test_db"
)

if test_url.database != "washflow_test_db":
    raise RuntimeError("Refusing to seed a non-test database.")

engine = create_engine(test_url)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def seed_vehicle_test_data():
    with SessionLocal() as db:
        try:
            customer = Customer(
                business_id=1,
                customer_type="individual",
                first_name="Independent",
                last_name="TestCustomer",
                email="independent-test@example.com",
                phone="0000000001",
            )

            db.add(customer)
            db.flush()

            vehicle_one = Vehicle(
                business_id=1,
                customer_id=customer.id,
                registration_number="INDEP-001",
                make="Toyota",
                model="Yaris",
                year=2022,
                colour="Blue",
            )

            vehicle_two = Vehicle(
                business_id=1,
                customer_id=customer.id,
                registration_number="INDEP-002",
                make="Ford",
                model="Fiesta",
                year=2021,
                colour="Red",
            )

            db.add_all([vehicle_one, vehicle_two])
            db.commit()

            print("Independent vehicle test data created.")
            print("Database: washflow_test_db")
            print("Customer ID:", customer.id)
            print("Vehicle 1 ID:", vehicle_one.id)
            print("Vehicle 2 ID:", vehicle_two.id)

        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    try:
        seed_vehicle_test_data()
    finally:
        engine.dispose()
