import pytest

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings


@pytest.fixture(scope="session")
def test_engine():
    # Always target the dedicated automated-test database.
    test_url = make_url(settings.database_url).set(
        database="washflow_pytest_db"
    )

    # Safety checks: ensure tests use the dedicated PostgreSQL database.
    if test_url.get_backend_name() != "postgresql":
        raise RuntimeError(
            "Tests blocked: PostgreSQL is required."
        )

    if test_url.database != "washflow_pytest_db":
        raise RuntimeError(
            "Tests blocked: incorrect database."
        )

    engine = create_engine(
        test_url,
        pool_pre_ping=True,
    )

    yield engine

    engine.dispose()


@pytest.fixture
def db(test_engine):
    # Give each test its own transaction.
    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        autoflush=False,
        autocommit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()