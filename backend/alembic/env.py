from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
import os
import sys
from sqlalchemy.sql.schema import Constraint, ForeignKeyConstraint, Column
from sqlalchemy import Integer, String, Boolean, ForeignKey 
from sqlalchemy import engine_from_config # Already imported, can remove duplicate
from alembic import context
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.config.setting import settings
from app.db.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

config.set_main_option("sqlalchemy.url",settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

from sqlalchemy.schema import Index, Table


def include_object(object, name, type_, reflected, compare_to):
    """
    Filter function to prevent foreign keys from being generated during migration.
    """

    # Check if the object is an Index and inspect its columns for ForeignKey
    if type_ == 'index' and isinstance(object, Index):
        for col in object.columns:
              # Check if the column has any foreign keys associated with it
            if hasattr(col, 'foreign_keys') and len(col.foreign_keys) > 0:
                return False
        return True

    # This is the primary logic: Check if the object being processed is explicitly a ForeignKeyConstraint
    if isinstance(object, ForeignKeyConstraint):
        return False
        
    # This check specifically targets the column type itself (e.g., when generating the sa.Column(...) line)
    if type_ == 'column' and isinstance(object, Column) and len(object.foreign_keys) > 0:
         return False
    # 4. Filter if the object is a Table that contains ForeignKeyConstraints
    if isinstance(object, Table):
        object.foreign_keys.clear()
        # Ensure that the constraints list doesn't contain FK constraints either
        object.constraints = {
            c for c in object.constraints 
            if not isinstance(c, ForeignKeyConstraint)
        }
        return True
    return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Crucial: include the include_object filter
        include_object=include_object 
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            # Crucial: include the include_object filter
            include_object=include_object 
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
