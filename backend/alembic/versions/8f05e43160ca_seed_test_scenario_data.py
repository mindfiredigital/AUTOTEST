"""seed test_scenario data

Revision ID: 8f05e43160ca
Revises: dce725f2abdb
Create Date: 2025-12-16 12:58:26.844637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = '8f05e43160ca'
down_revision: Union[str, Sequence[str], None] = 'dce725f2abdb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(f"""
        INSERT INTO test_scenario
            (id, page_id, title, data, type, category, created_on, created_by, updated_on, updated_by)
        VALUES
            (
                1,
                1,
                'Login Medium',
                '{
                    "email": "test@gmail.com",
                    "steps": ["Enter username", "Enter invalid password", "Click login"]
                }',
                'manual',
                'auth-negative',
                '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                1,
                '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                1
            ),
            (
                2,
                2,
                'About Page Load',
                '{
                    "expected_title": "About - Medium",
                    "steps": ["Navigate to about page", "Verify title"]
                }',
                'automated',
                'page-load',
                '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                1,
                '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                1
            );
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM test_scenario")

