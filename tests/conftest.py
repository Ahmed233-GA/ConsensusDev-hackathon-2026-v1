import os
import pytest
from pathlib import Path

# Force all automated tests to strictly use a dedicated test database
TEST_DB_PATH = Path(__file__).resolve().parent.parent / "test_consensusdev.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from gateway.database import configure_db, init_db
from gateway.seed_admin import seed_admin_user


@pytest.fixture(scope="session", autouse=True)
def setup_test_database_session():
    """
    Session-level fixture configuring an isolated SQLite test database for pytest.
    Guarantees the demo database (consensusdev.db) is NEVER touched during automated test execution.
    """
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    configure_db(TEST_DATABASE_URL)
    init_db()
    seed_admin_user()

    yield

    # Clean up test database connection if needed
    configure_db(TEST_DATABASE_URL)
