from sqlalchemy import text


def test_connection_uses_dedicated_test_database(db):
    database_name = db.execute(
        text("SELECT current_database()")
    ).scalar_one()

    assert database_name == "washflow_pytest_db"