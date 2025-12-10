"""create page_link_test_case table

Revision ID: aec2dfb89914
Revises: 87652f95e2e3
Create Date: 2025-12-10 19:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aec2dfb89914'
down_revision: Union[str, Sequence[str], None] = '87652f95e2e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'page_link_test_case',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('page_link_id', sa.Integer(), nullable=False, index=True),
        sa.Column('test_case_id_source', sa.Integer(), nullable=True, index=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default=sa.text('0')),
    )

    # op.execute("CREATE INDEX IF NOT EXISTS ix_page_link_test_case_page_link_id ON page_link_test_case (page_link_id)")
    # op.execute("CREATE INDEX IF NOT EXISTS ix_page_link_test_case_test_case_id_source ON page_link_test_case (test_case_id_source)")

def downgrade() -> None:
    op.drop_table('page_link_test_case')
