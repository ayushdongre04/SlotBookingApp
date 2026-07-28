"""
Alembic environment configuration.

This module is executed by Alembic whenever a migration command is run.

Responsibilities:
- Load the application's database configuration.
- Import all SQLAlchemy models so they are registered with Base.metadata.
- Expose metadata for Alembic's autogeneration feature.
- Execute database schema migrations.

Alembic supports two execution modes:

1. Offline mode
   - Does not connect to the database.
   - Generates SQL migration scripts that can be reviewed or executed manually.

2. Online mode
   - Connects directly to the database.
   - Executes migration operations immediately.

Although the application uses SQLAlchemy's AsyncEngine for handling
concurrent API requests, Alembic intentionally uses a synchronous engine.
Schema migrations are administrative tasks executed sequentially and do not
benefit from asynchronous execution. Using a synchronous engine keeps the
migration environment simpler, avoids platform-specific asyncio issues (such
as those on Windows), and follows the approach commonly used in production
SQLAlchemy applications.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.core.base import Base
from app.core.config import settings

# Import all models so SQLAlchemy registers them in Base.metadata.
# These imports are intentionally unused.
from app.booking import model as booking_models  # noqa: F401
from app.providers import model as provider_models  # noqa: F401
from app.slots import model as slot_models  # noqa: F401

# Alembic configuration object.
config = context.config

# Override the database URL from application settings.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Configure logging using alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata used for autogenerating migrations.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations without opening a database connection.

    Alembic generates SQL statements instead of executing them.
    This mode is useful when SQL scripts need to be reviewed or
    executed manually by a DBA.
    """

    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """
    Configure Alembic using an active database connection and
    execute all pending migrations.

    This function is intentionally synchronous because Alembic's
    migration API is synchronous. SQLAlchemy's AsyncEngine bridges
    to this function through connection.run_sync().
    """

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations against a live database.

    Alembic itself is synchronous. Even if the application uses
    AsyncEngine, migrations are executed through a synchronous engine
    because schema migrations are administrative tasks rather than
    request-processing code.

    Using a synchronous engine avoids platform-specific asyncio issues
    (such as Windows ProactorEventLoop compatibility) while remaining
    fully compatible with SQLAlchemy metadata.
    """

    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        pool_pre_ping=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
