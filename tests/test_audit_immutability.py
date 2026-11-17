import pytest

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.models import Business


def test_audit_logs_reject_mutation_operations(test_engine):
    # Create a business and audit record inside one transaction.
    with test_engine.begin() as connection:
        business = Business(
            name="Pytest Audit Immutability Business"
        )

        # Insert the business using its ORM table definition.
        result = connection.execute(
            Business.__table__.insert().values(
                name=business.name,
            ).returning(Business.id)
        )
        business_id = result.scalar_one()

        audit_id = connection.execute(
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
                    'Temporary audit immutability test'
                )
                RETURNING id
            """),
            {"business_id": business_id},
        ).scalar_one()

        operations = {
            "UPDATE": (
                """
                UPDATE audit_logs
                SET description = 'Modified audit record'
                WHERE id = :audit_id
                """,
                "Audit log records are immutable. UPDATE and DELETE are prohibited.",
            ),
            "DELETE": (
                """
                DELETE FROM audit_logs
                WHERE id = :audit_id
                """,
                "Audit log records are immutable. UPDATE and DELETE are prohibited.",
            ),
            "TRUNCATE": (
                "TRUNCATE TABLE audit_logs",
                "Audit log records cannot be truncated.",
            ),
        }

        for operation, (statement, expected_message) in operations.items():
            with pytest.raises(DBAPIError) as error:
                with connection.begin_nested():
                    connection.execute(
                        text(statement),
                        {"audit_id": audit_id},
                    )

            original_error = error.value.orig
            actual_message = str(original_error)

            assert expected_message in actual_message, (
                f"{operation} failed for an unexpected reason: "
                f"{actual_message}"
            )

        # Confirm that the original audit record remains unchanged.
        remaining_record = connection.execute(
            text("""
                SELECT description
                FROM audit_logs
                WHERE id = :audit_id
            """),
            {"audit_id": audit_id},
        ).scalar_one()

        assert remaining_record == (
            "Temporary audit immutability test"
        )
