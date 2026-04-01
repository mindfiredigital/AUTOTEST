"""drop script_path column from test_scenario

Revision ID: h1a2b3c4d5e6
Revises: g5d9e3f8c2b1
Create Date: 2026-04-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'g5d9e3f8c2b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('test_scenario', 'script_path')


def downgrade() -> None:
    op.add_column(
        'test_scenario',
        sa.Column('script_path', sa.String(length=255), nullable=True),
    )
