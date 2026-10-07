"""Explicit migration entry point; a caller may supply an isolated connection."""
from alembic import context
from voynich.storage.database import make_engine
from voynich.storage.schema import metadata

def migrate(connection):
    context.configure(connection=connection, target_metadata=metadata,
                      version_table="lab_alembic_version")
    with context.begin_transaction():
        context.run_migrations()

connection = context.config.attributes.get("connection")
if connection is not None:
    migrate(connection)
else:
    engine = make_engine()
    try:
        with engine.connect() as connection:
            migrate(connection)
    finally:
        engine.dispose()
