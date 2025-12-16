"""seed page_link data

Revision ID: 2a631101e1f8
Revises: e5aefd4063bf
Create Date: 2025-12-16 13:08:23.212439

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a631101e1f8'
down_revision: Union[str, Sequence[str], None] = 'e5aefd4063bf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
        INSERT INTO page_link
            (id, page_id_source, test_scenario_id_source, page_id_target, event_selector, event_description)
        VALUES
            (
                1,
                1,
                1,
                2,
                'button#login',
                'Click login button redirects to home'
            ),
               (
                2,
                2,
                1,
                2,
                'button#about',
                'Click about button redirects to about page'
            );
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM page_link")
