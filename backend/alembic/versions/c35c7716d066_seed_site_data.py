"""seed site data

Revision ID: c35c7716d066
Revises: 0fd2c8c45002
Create Date: 2025-12-10 23:56:48.578471

"""
import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = 'c35c7716d066'
down_revision: Union[str, Sequence[str], None] = '0fd2c8c45002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    # Insert seed data
    op.execute(f"""
        INSERT INTO site
            (site_title, site_url, status, created_on, created_by)
        VALUES
            ('Medium', 'https://medium.com', 'New', '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 1),
            ('Riverml', 'https://riverml.xyz/latest', 'Active', '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 1),
            ('Medium Find', 'https://medium.com/@fimd', 'Inactive', '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 2);
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM site")
