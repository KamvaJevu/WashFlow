
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import User, BusinessMembership


test_url = make_url(settings.database_url).set(
    database="washflow_test_db"
)

if test_url.database != "washflow_test_db":
    raise RuntimeError("Refusing to use a non-test database.")

engine = create_engine(test_url)

try:
    with Session(engine) as db:

        existing_user = db.scalar(
            select(User).where(
                User.email == "archival-staff@example.com"
            )
        )

        if existing_user:
            raise RuntimeError(
                "Test Staff user already exists. No changes made."
            )

        staff_user = User(
            first_name="Test",
            last_name="Staff",
            email="archival-staff@example.com",
            password_hash="NOT_A_REAL_PASSWORD_HASH",
            is_active=True,
        )

        db.add(staff_user)
        db.flush()

        staff_membership = BusinessMembership(
            business_id=1,
            user_id=staff_user.id,
            role="staff",
            status="active",
        )

        db.add(staff_membership)
        db.commit()

        print("Test Staff user created.")
        print("User ID:", staff_user.id)
        print("Membership ID:", staff_membership.id)
        print("Business ID:", staff_membership.business_id)
        print("Role:", staff_membership.role)
        print("Status:", staff_membership.status)

finally:
    engine.dispose()
