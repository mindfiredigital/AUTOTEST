"""seed role data

Revision ID: 821cca5fc78c
Revises: d2d1096b78c2
Create Date: 2025-12-16 14:27:57.448383

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa, json


# revision identifiers, used by Alembic.
revision: str = '821cca5fc78c'
down_revision: Union[str, Sequence[str], None] = 'd2d1096b78c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()

    roles = [
        {
            "id": 1,
            "type": "Admin",
            "access": """{
                "profile": true,
                "site": true,
                "page": true,
                "test_scenario": true,
                "test_case": true,
                "test_configuration": true,
                "test_environment": true,
                "test_suite": true,
                "test_schedule": true,
                "role": true,
                "user": true,
                "settings": true
            }"""
        },
        {
            "id": 2,
            "type": "User",
            "access": """{
                "profile": true,
                "site": true,
                "page": true,
                "test_scenario": true,
                "test_case": true,
                "test_configuration": true,
                "test_environment": true,
                "test_suite": true,
                "test_schedule": true
            }"""
        }
    ]

    sql = sa.text("""
        INSERT INTO role (id, type, access)
        VALUES (:id, :type, :access)
        ON DUPLICATE KEY UPDATE
            type = VALUES(type),
            access = VALUES(access)
    """)

    for r in roles:
        conn.execute(sql, r)

def downgrade():
    op.execute("DELETE FROM role WHERE id IN (1, 2)")