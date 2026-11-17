from sqlalchemy.engine import make_url
from app.core.config import settings
from alembic.config import Config
from alembic import command

test_url = make_url(settings.database_url).set(
    database="washflow_test_db"
)

config = Config("alembic.ini")
config.attributes["database_url"] = test_url.render_as_string(
    hide_password=False
)

command.upgrade(config, "head")
