
from sqlalchemy.engine import make_url
from alembic.config import Config
from alembic import command

from app.core.config import settings


# Build a separate URL for automated testing.
test_url = make_url(settings.database_url).set(
    database="washflow_pytest_db"
)

# Safety check: never migrate another database.
if test_url.database != "washflow_pytest_db":
    raise RuntimeError(
        "Migration blocked: incorrect test database."
    )

# Configure Alembic to use the dedicated test database.
config = Config("alembic.ini")

config.attributes["database_url"] = test_url.render_as_string(
    hide_password=False
)

print("Running migrations against:", test_url.database)

command.upgrade(config, "head")

print("Automated-test database migrations completed.")
