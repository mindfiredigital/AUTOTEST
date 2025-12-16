"""seed page_link_test_case data

Revision ID: add438d3185b
Revises: 2a631101e1f8
Create Date: 2025-12-16 13:09:58.676953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add438d3185b'
down_revision: Union[str, Sequence[str], None] = '2a631101e1f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        INSERT INTO page_link_test_case
            (page_link_id, test_case_id_source, verified)
        VALUES
            (1, 1, 1),
            (2, 1, 0);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM page_link_test_case")
