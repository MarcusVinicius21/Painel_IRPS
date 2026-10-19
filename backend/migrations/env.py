from alembic import context
from sqlalchemy import create_engine
from app.config import load_settings
engine=create_engine(load_settings().owner_database_url.get_secret_value(),hide_parameters=True)
with engine.connect() as connection:
 context.configure(connection=connection,target_metadata=None)
 with context.begin_transaction():context.run_migrations()

