
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "37f91b7b783c"
down_revision: Union[str, Sequence[str], None] = "b568c93327bd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Protect audit logs from UPDATE, DELETE and TRUNCATE."""

    op.execute("""
        CREATE FUNCTION prevent_audit_log_mutation()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION
                'Audit log records are immutable. UPDATE and DELETE are prohibited.';
        END;
        $$;
    """)

    op.execute("""
        CREATE FUNCTION prevent_audit_log_truncate()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RAISE EXCEPTION
                'Audit log records cannot be truncated.';
        END;
        $$;
    """)

    op.execute("""
        CREATE TRIGGER trg_audit_logs_immutable
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_mutation();
    """)

    op.execute("""
        CREATE TRIGGER trg_audit_logs_no_truncate
        BEFORE TRUNCATE ON audit_logs
        FOR EACH STATEMENT
        EXECUTE FUNCTION prevent_audit_log_truncate();
    """)


def downgrade() -> None:
    """Remove audit-log mutation protection."""

    op.execute("""
        DROP TRIGGER IF EXISTS trg_audit_logs_no_truncate
        ON audit_logs;
    """)

    op.execute("""
        DROP TRIGGER IF EXISTS trg_audit_logs_immutable
        ON audit_logs;
    """)

    op.execute("""
        DROP FUNCTION IF EXISTS prevent_audit_log_truncate();
    """)

    op.execute("""
        DROP FUNCTION IF EXISTS prevent_audit_log_mutation();
    """)
