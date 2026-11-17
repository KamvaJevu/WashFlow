
from app.db.database import engine, SessionLocal, Base

try:
    with engine.connect() as connection:
        print("PostgreSQL connection successful!")
        print("Database engine:", engine.dialect.name)
        print("Session factory:", SessionLocal is not None)
        print("Model base:", Base.__name__)

except Exception as error:
    print("Database connection failed:")
    print(error)

finally:
    engine.dispose()
