
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.database_url)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT current_database()"))
        database_name = result.scalar()

        print("PostgreSQL connection successful!")
        print("Connected database:", database_name)

except Exception as error:
    print("Database connection failed:")
    print(error)

finally:
    engine.dispose()
