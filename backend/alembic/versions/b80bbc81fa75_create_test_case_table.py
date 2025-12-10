"""create test case table

Revision ID: b80bbc81fa75
Revises: 400c91b59001
Create Date: 2025-12-10 19:25:38.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b80bbc81fa75'
down_revision: Union[str, Sequence[str], None] = '400c91b59001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'test_case',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('page_id', sa.Integer(), nullable=False, index=True),
        sa.Column('test_scenario_id', sa.Integer(), nullable=False, index=True),
        sa.Column('last_test_execution_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('type', sa.Enum('auto-generated', 'manual', name='testcasetypeenum'), nullable=False, server_default='auto-generated'),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('expected_outcome', sa.JSON(), nullable=True),
        sa.Column('validation', sa.JSON(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('is_valid_default', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_on', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_on', sa.DateTime(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
    )

    # op.execute("CREATE INDEX IF NOT EXISTS ix_test_case_page_id ON test_case (page_id)")
    # op.execute("CREATE INDEX IF NOT EXISTS ix_test_case_test_scenario_id ON test_case (test_scenario_id)")
    # op.execute("CREATE INDEX IF NOT EXISTS ix_test_case_last_test_execution_id ON test_case (last_test_execution_id)")


def downgrade() -> None:
    op.drop_table('test_case')
