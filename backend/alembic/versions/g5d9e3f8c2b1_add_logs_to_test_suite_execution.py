"""add logs column to test_suite_execution

Revision ID: g5d9e3f8c2b1
Revises: f4c8b2a1d6e9
Create Date: 2026-03-31 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'g5d9e3f8c2b1'
down_revision: Union[str, Sequence[str], None] = 'f4c8b2a1d6e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_columns(table: str) -> set[str]:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    return {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    """Add logs TEXT column to test_suite_execution."""
    if 'logs' not in _existing_columns('test_suite_execution'):
        op.add_column(
            'test_suite_execution',
            sa.Column('logs', sa.Text(), nullable=True)
        )


def downgrade() -> None:
    """Remove logs column."""
    if 'logs' in _existing_columns('test_suite_execution'):
        op.drop_column('test_suite_execution', 'logs')
