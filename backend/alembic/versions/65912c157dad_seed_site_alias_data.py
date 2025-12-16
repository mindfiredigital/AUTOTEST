"""seed site_alias data

Revision ID: 65912c157dad
Revises: c35c7716d066
Create Date: 2025-12-16 12:23:17.518801

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65912c157dad'
down_revision: Union[str, Sequence[str], None] = 'c35c7716d066'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Insert seed data
    op.execute(f"""
        INSERT INTO site_alias (id, site_id, site_alias_title, site_alias_url)
        VALUES
            (1, 1, 'Medium Stage', 'https://stage.medium.com'),
            (2, 1, 'Medium QA', 'https://qa.medium.com'),
            (3, 2, 'Riverml Dev', 'https://dev.riverml.xyz');
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM site_alias")

