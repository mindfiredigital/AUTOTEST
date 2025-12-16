"""seed user data

Revision ID: 131416675501
Revises: 933a97f90659
Create Date: 2025-12-16 13:19:01.870405

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = '131416675501'
down_revision: Union[str, Sequence[str], None] = '933a97f90659'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM user")
