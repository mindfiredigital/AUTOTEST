"""seed test_execution data

Revision ID: 0c948858bb77
Revises: add438d3185b
Create Date: 2025-12-16 13:10:45.223099

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = '0c948858bb77'
down_revision: Union[str, Sequence[str], None] = 'add438d3185b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute(
        sa.text(f"""
            INSERT INTO test_execution
                (page_id, test_scenario_id, test_case_id, status, logs, executed_on, executed_by)
            VALUES
                (
                    1,
                    1,
                    1,
                    'Passed',
                    'Login failed as expected',
                    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    1
                ),
                (
                    2,
                    2,
                    NULL,
                    'Failed',
                    'Page title did not match expected',
                    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    1
                ),
                (
                    1,
                    1,
                    1,
                    'Passed',
                    'Login failed as expected on second run',
                    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    2
                ),
                (
                    2,
                    2,
                    NULL,
                    'Passed',
                    'Page title matched expected on second run',
                    '{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    2
                );
        """)
    )


def downgrade():
    op.execute("""
        DELETE FROM test_execution
        WHERE page_id IN (1, 2)
          AND test_scenario_id IN (1, 2);
    """)