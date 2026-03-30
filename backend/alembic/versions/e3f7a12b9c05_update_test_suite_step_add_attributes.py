"""update test_suite_step: add node_type, test_suite_step_attribute, make page_id/scenario_id nullable

Revision ID: e3f7a12b9c05
Revises: 54a59124c36a
Create Date: 2026-03-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'e3f7a12b9c05'
down_revision: Union[str, Sequence[str], None] = '54a59124c36a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _existing_columns(table: str) -> set[str]:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    return {col["name"] for col in inspector.get_columns(table)}


def upgrade() -> None:
    """Add node_type and test_suite_step_attribute columns; make page_id/scenario_id nullable."""
    existing = _existing_columns('test_suite_step')

    if 'node_type' not in existing:
        op.add_column(
            'test_suite_step',
            sa.Column('node_type', sa.String(50), nullable=True)
        )

    if 'test_suite_step_attribute' not in existing:
        op.add_column(
            'test_suite_step',
            sa.Column('test_suite_step_attribute', sa.JSON(), nullable=True)
        )

    op.alter_column('test_suite_step', 'page_id',
                    existing_type=sa.Integer(), nullable=True)
    op.alter_column('test_suite_step', 'scenario_id',
                    existing_type=sa.Integer(), nullable=True)
    op.alter_column('test_suite_step', 'label',
                    existing_type=sa.String(50), type_=sa.String(200), nullable=True)


def downgrade() -> None:
    """Revert schema changes."""
    op.alter_column('test_suite_step', 'label',
                    existing_type=sa.String(200), type_=sa.String(50), nullable=False)
    op.alter_column('test_suite_step', 'scenario_id',
                    existing_type=sa.Integer(), nullable=False)
    op.alter_column('test_suite_step', 'page_id',
                    existing_type=sa.Integer(), nullable=False)

    existing = _existing_columns('test_suite_step')
    if 'test_suite_step_attribute' in existing:
        op.drop_column('test_suite_step', 'test_suite_step_attribute')
    if 'node_type' in existing:
        op.drop_column('test_suite_step', 'node_type')
