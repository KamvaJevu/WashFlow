
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import engine


with engine.connect() as connection:
    transaction = connection.begin()

    try:
        business_id = connection.scalar(
            text("SELECT id FROM businesses LIMIT 1")
        )

        if business_id is None:
            print("No business exists for the protection test.")
        else:
            audit_id = connection.scalar(
                text("""
                    INSERT INTO audit_logs (
                        business_id,
                        action_type,
                        entity_type,
                        entity_id,
                        description
                    )
                    VALUES (
                        :business_id,
                        'TEST',
                        'test',
                        999999,
                        'Temporary audit protection test'
                    )
                    RETURNING id
                """),
                {"business_id": business_id},
            )

            print("Temporary audit record created:", audit_id)

            tests = {
                "UPDATE": """
                    UPDATE audit_logs
                    SET description = 'Modified test record'
                    WHERE id = :audit_id
                """,
                "DELETE": """
                    DELETE FROM audit_logs
                    WHERE id = :audit_id
                """,
                "TRUNCATE": "TRUNCATE TABLE audit_logs",
            }

            for operation, statement in tests.items():
                try:
                    with connection.begin_nested():
                        connection.execute(
                            text(statement),
                            {"audit_id": audit_id},
                        )
                    print(operation, "was NOT blocked.")
                except SQLAlchemyError:
                    print(operation, "successfully blocked.")

    finally:
        transaction.rollback()
        print("Test transaction rolled back.")
