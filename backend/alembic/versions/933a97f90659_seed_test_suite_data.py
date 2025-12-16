"""seed test_suite data

Revision ID: 933a97f90659
Revises: 0c948858bb77
Create Date: 2025-12-16 13:11:43.220440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = '933a97f90659'
down_revision: Union[str, Sequence[str], None] = '0c948858bb77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(f"""
        INSERT INTO test_suite
            (site_id, title, created_on, created_by)
        VALUES
            (1, 'Medium Login Suite', '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 1),
            (1, 'Medium About Suite', '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 1),
            (2, 'Riverml Dev Suite', '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 2),
            (2, 'Riverml Prod Suite', '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 2),
            (1, 'Medium Membership Suite', '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 1);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM test_suite")
