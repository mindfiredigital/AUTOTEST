"""seed test_case data

Revision ID: e5aefd4063bf
Revises: 8f05e43160ca
Create Date: 2025-12-16 13:07:12.294988

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = 'e5aefd4063bf'
down_revision: Union[str, Sequence[str], None] = '8f05e43160ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(f"""
        INSERT INTO test_case
            (id, page_id, test_scenario_id, title, type, data, expected_outcome, validation, is_valid, is_valid_default, created_on, created_by, updated_on, updated_by)
        VALUES
            (
                1,
                1,
                1,
                'TC_Invalid_Password',
                'manual',
                '{"userName":"demo","password":"wrong"}',
                '{"expected":"Login should fail"}',
                '{"validate":"error message shown"}',
                1,
                1,
                '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                1,
                '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                1
            );
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM test_case")
