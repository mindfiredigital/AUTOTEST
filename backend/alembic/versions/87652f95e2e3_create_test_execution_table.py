"""create test execution table

Revision ID: 87652f95e2e3
Revises: b80bbc81fa75
Create Date: 2025-12-10 19:28:38.841182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87652f95e2e3'
down_revision: Union[str, Sequence[str], None] = 'b80bbc81fa75'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'test_execution',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('page_id', sa.Integer(), nullable=False, index=True),
        sa.Column('test_scenario_id', sa.Integer(), nullable=False, index=True),
        sa.Column('test_case_id', sa.Integer(), nullable=True, index=True),
        sa.Column('test_suite_id', sa.Integer(), nullable=True, index=True),
        sa.Column('status', sa.Enum('NOne', 'Passed', 'Partially Passed', 'Failed', name='testexecutionstatusenum'), nullable=True),
        sa.Column('logs', sa.Text(), nullable=True),
        sa.Column('executed_on', sa.DateTime(), nullable=True),
        sa.Column('executed_by', sa.Integer(), sa.ForeignKey('user.id'), nullable=True),
    )

    # Create indexes (SQLAlchemy will also do it via column index=True but this is explicit)
    # op.execute("CREATE INDEX IF NOT EXISTS ix_test_execution_page_id ON test_execution (page_id)")
    # op.execute("CREATE INDEX IF NOT EXISTS ix_test_execution_test_scenario_id ON test_execution (test_scenario_id)")
    # op.execute("CREATE INDEX IF NOT EXISTS ix_test_execution_test_case_id ON test_execution (test_case_id)")
    # op.execute("CREATE INDEX IF NOT EXISTS ix_test_execution_test_suite_id ON test_execution (test_suite_id)")

def downgrade() -> None:
    op.drop_table('test_execution')
