"""update test_suite_step: add node_type, test_suite_step_attribute, make page_id/scenario_id nullable

Revision ID: e3f7a12b9c05
Revises: 54a59124c36a
Create Date: 2026-03-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3f7a12b9c05'
down_revision: Union[str, Sequence[str], None] = '54a59124c36a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add node_type and test_suite_step_attribute columns; make page_id/scenario_id nullable."""

    # Add node_type column to track the type of node (start, step, branch, end, suite_ref)
    op.add_column(
        'test_suite_step',
        sa.Column('node_type', sa.String(50), nullable=True)
    )

    # Add test_suite_step_attribute JSON column to store site attributes for the step
    op.add_column(
        'test_suite_step',
        sa.Column('test_suite_step_attribute', sa.JSON(), nullable=True)
    )

    # Make page_id nullable (branch/end/start nodes don't have a page reference)
    op.alter_column('test_suite_step', 'page_id', nullable=True)

    # Make scenario_id nullable (branch/end/start nodes don't have a scenario reference)
    op.alter_column('test_suite_step', 'scenario_id', nullable=True)

    # Make label allow longer strings (flow node labels can exceed 50 chars)
    op.alter_column('test_suite_step', 'label', type_=sa.String(200), nullable=True)


def downgrade() -> None:
    """Revert schema changes."""

    op.alter_column('test_suite_step', 'label', type_=sa.String(50), nullable=False)
    op.alter_column('test_suite_step', 'scenario_id', nullable=False)
    op.alter_column('test_suite_step', 'page_id', nullable=False)
    op.drop_column('test_suite_step', 'test_suite_step_attribute')
    op.drop_column('test_suite_step', 'node_type')
