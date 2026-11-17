
from sqlalchemy.engine import make_url
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import (
    Business,
    User,
    BusinessMembership,
    Customer,
    Vehicle,
)


# Always target the isolated test database.
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


def seed_test_data():
    db = SessionLocal()

    try:
        # Create test business.
        business = Business(
            name="WashFlow Archival Test Business",
            email="archival-test@example.com",
            status="active",
        )
        db.add(business)
        db.flush()

        # Create dummy test user.
        user = User(
            first_name="Test",
            last_name="Owner",
            email="archival-owner@example.com",
            password_hash="NOT_A_REAL_PASSWORD_HASH",
            is_active=True,
        )
        db.add(user)
        db.flush()

        # Give the user an active Owner membership.
        membership = BusinessMembership(
            business_id=business.id,
            user_id=user.id,
            role="owner",
            status="active",
        )
        db.add(membership)
        db.flush()

        # Create an individual customer.
        customer = Customer(
            business_id=business.id,
            customer_type="individual",
            first_name="Test",
            last_name="Customer",
            email="customer@example.com",
            phone="0000000000",
        )
        db.add(customer)
        db.flush()

        # Create two vehicles for the customer.
        vehicle_one = Vehicle(
            business_id=business.id,
            customer_id=customer.id,
            registration_number="TEST-001",
            make="Toyota",
            model="Corolla",
            year=2020,
            colour="White",
        )

        vehicle_two = Vehicle(
            business_id=business.id,
            customer_id=customer.id,
            registration_number="TEST-002",
            make="Volkswagen",
            model="Polo",
            year=2021,
            colour="Silver",
        )

        db.add_all([vehicle_one, vehicle_two])
        db.commit()

        print("Test data created successfully.")
        print("Database: washflow_test_db")
        print("Business ID:", business.id)
        print("User ID:", user.id)
        print("Membership ID:", membership.id)
        print("Customer ID:", customer.id)
        print("Vehicle 1 ID:", vehicle_one.id)
        print("Vehicle 2 ID:", vehicle_two.id)

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    seed_test_data()
