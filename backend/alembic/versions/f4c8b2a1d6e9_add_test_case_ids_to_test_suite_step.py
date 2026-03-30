"""add test_case_ids column to test_suite_step

Revision ID: f4c8b2a1d6e9
Revises: e3f7a12b9c05
Create Date: 2026-03-30 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'f4c8b2a1d6e9'
down_revision: Union[str, Sequence[str], None] = 'e3f7a12b9c05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_columns(table: str) -> set[str]:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    return {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    """Add test_case_ids column (comma-separated IDs) to test_suite_step."""
    if 'test_case_ids' not in _existing_columns('test_suite_step'):
        op.add_column(
            'test_suite_step',
            sa.Column('test_case_ids', sa.String(1000), nullable=True)
        )


def downgrade() -> None:
    """Remove test_case_ids column."""
    if 'test_case_ids' in _existing_columns('test_suite_step'):
        op.drop_column('test_suite_step', 'test_case_ids')
