"""seed page data

Revision ID: dce725f2abdb
Revises: 65912c157dad
Create Date: 2025-12-16 12:52:53.156356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = 'dce725f2abdb'
down_revision: Union[str, Sequence[str], None] = '65912c157dad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(f"""
        INSERT INTO page
            (id, site_id, page_url, status, page_title, page_source, page_metadata, created_on, created_by, updated_on, updated_by)
        VALUES
            (1, 1, 'https://medium.com/login', 'New', 'Login', '<html>login</html>', '{{}}', '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 1, '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 1),
            (2, 1, 'https://medium.com/about', 'New', 'About', '<html>about</html>', '{{}}', '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 1, '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 1),
            (3, 1, 'https://medium.com/membership', 'New', 'Membership', '<html>membership</html>', '{{}}', '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 1, '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 1);
    """
)
def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM page")
