from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from datetime import datetime

revision: str = 'd2d1096b78c2'
down_revision: Union[str, Sequence[str], None] = '131416675501'
branch_labels = None
depends_on = None


def upgrade():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = op.get_bind()

    settings = [
        {
            "key": "app_name",
            "title": "Application Name",
            "description": "Name of the application shown in UI",
            "type": "Text",
            "possible_values": None,
            "default_value": "AutoTest Platform",
        },
        {
            "key": "app_environment",
            "title": "Application Environment",
            "description": "Current environment in which application is running",
            "type": "Dropdown",
            "possible_values": "development|staging|production",
            "default_value": "development",
        },
        {
            "key": "default_browser",
            "title": "Default Browser",
            "description": "Browser used for executing automated tests",
            "type": "Dropdown",
            "possible_values": "chrome|firefox|edge",
            "default_value": "chrome",
        },
        {
            "key": "page_load_timeout",
            "title": "Page Load Timeout (seconds)",
            "description": "Maximum wait time for page load during test execution",
            "type": "Number",
            "possible_values": None,
            "default_value": "30",
        },
        {
            "key": "selenium_grid_enabled",
            "title": "Enable Selenium Grid",
            "description": "Enable or disable Selenium Grid execution",
            "type": "Radio Button",
            "possible_values": "true|false",
            "default_value": "false",
        },
        {
            "key": "max_login_attempts",
            "title": "Maximum Login Attempts",
            "description": "Number of failed login attempts before account lock",
            "type": "Number",
            "possible_values": None,
            "default_value": "5",
        },
    ]

    sql = sa.text("""
        INSERT INTO setting (
            `key`,
            title,
            description,
            type,
            possible_values,
            default_value,
            actual_value,
            updated_on,
            updated_by
        )
        VALUES (
            :key,
            :title,
            :description,
            :type,
            :possible_values,
            :default_value,
            :default_value,
            :updated_on,
            1
        )
        ON DUPLICATE KEY UPDATE
            title = VALUES(title),
            description = VALUES(description),
            type = VALUES(type),
            possible_values = VALUES(possible_values),
            default_value = VALUES(default_value),
            updated_on = VALUES(updated_on),
            updated_by = 1
    """)

    for s in settings:
        conn.execute(sql, {**s, "updated_on": now})


def downgrade():
    op.execute("""
        DELETE FROM setting
        WHERE `key` IN (
            'app_name',
            'app_environment',
            'default_browser',
            'page_load_timeout',
            'selenium_grid_enabled',
            'max_login_attempts'
        )
    """)
