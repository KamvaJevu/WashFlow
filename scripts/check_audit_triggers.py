from sqlalchemy import text

from app.db.database import engine

EXPECTED_DATABASE = "washflow_db"

def main():
    configured_database = engine.url.database

    if configured_database != EXPECTED_DATABASE:
        raise RuntimeError(
            "Unsafe database connection. "
            f"Expected '{EXPECTED_DATABASE}', "
            f"but found '{configured_database}'."
        )

    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT tgname
                FROM pg_trigger
                WHERE tgrelid = 'audit_logs'::regclass
                  AND NOT tgisinternal
                ORDER BY tgname
            """)
        )

        triggers = [row[0] for row in result]

        print("Connected database:", configured_database)
        print("Registered audit triggers:", triggers)

if __name__ == "__main__":
    main()