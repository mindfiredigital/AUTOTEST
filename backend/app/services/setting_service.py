"""Service layer for settings and setting categories.

Contains operations to retrieve categories/settings and to update
their actual values singly or in bulk.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc
from datetime import datetime, timezone
from shared_orm.models.setting_category import SettingCategory
from shared_orm.models.setting import Setting
from sqlalchemy import func
from shared_orm.models.test_case import TestCase
from shared_orm.models.test_scenario import TestScenario
from app.schemas.setting_schema import SettingResponse
from app.config.logger import logger


class SettingService:
    """Business logic for settings management."""

    def get_setting_by_category(
        self,
        setting_category_id: int,
        db: Session,
    ):
        """Return all settings for a category or raise 404 if none."""
        logger.debug("Fetching settings for category_id=%s", setting_category_id)
        settings = db.query(Setting).filter(Setting.setting_category_id == setting_category_id).all()
        if not settings:
            logger.warning("No settings found for category_id=%s", setting_category_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No settings found for the given category."
            )
        return settings
    
    def get_all_setting_categories(
        self,
        db: Session,
    ):
        """Return all setting categories."""
        logger.debug("Fetching all setting categories")
        categories = db.query(SettingCategory).all()
        return categories
    
    def get_setting_category_by_id(
        self,
        setting_category_id: int,
        db: Session,
    ):
        """Return a setting category by ID or raise 404."""
        logger.debug("Fetching setting category id=%s", setting_category_id)
        category = db.query(SettingCategory).filter(SettingCategory.id == setting_category_id).first()
        if not category:
            logger.warning("Setting category not found id=%s", setting_category_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Setting category not found."
            )
        return category
    
    def get_setting_by_id(
        self,
        setting_id: int,
        db: Session,
    ):
        """Return a setting by ID or raise 404."""
        logger.debug("Fetching setting id=%s", setting_id)
        setting = db.query(Setting).filter(Setting.id == setting_id).first()
        if not setting:
            logger.warning("Setting not found id=%s", setting_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Setting not found."
            )
        return setting
    
    def get_all_settings(
        self,
        db: Session,
    ):
        """Return all settings."""
        logger.debug("Fetching all settings")
        settings = db.query(Setting).all()
        return settings

    def update_actual_value(
        self,
        setting_id: int,
        actual_value: str,
        db: Session,
    ):
        """Update the `actual_value` for a single setting and return it."""
        logger.info("Updating setting id=%s actual_value=%s", setting_id, actual_value)
        setting = db.query(Setting).filter(Setting.id == setting_id).first()

        if not setting:
            logger.warning("Attempted update on missing setting id=%s", setting_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Setting not found"
            )

        setting.actual_value = actual_value
        db.commit()
        db.refresh(setting)

        logger.info("Updated setting id=%s", setting_id)
        return setting
    def update_actual_values_by_category(
        self,
        setting_category_id: int,
        updates: list,
        db: Session,
        updated_by_user_id: int,
    ):
        """Bulk update actual values for settings in a category.

        Validates input, updates records, and commits. Raises HTTP
        errors for invalid input or on failure.
        """
        if not updates:
            logger.warning("Bulk update called with empty updates for category_id=%s", setting_category_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No settings provided for update."
            )

        settings = (
            db.query(Setting)
            .filter(Setting.setting_category_id == setting_category_id)
            .all()
        )

        if not settings:
            logger.warning("No settings found for category_id=%s", setting_category_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No settings found for this category."
            )

        settings_map = {s.id: s for s in settings}

        for item in updates:
            if item.id not in settings_map:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Setting ID {item.id} does not belong to this category."
                )

        logger.info("Bulk updating %s settings for category_id=%s", len(updates), setting_category_id)
        try:
            for item in updates:
                setting = settings_map[item.id]
                setting.actual_value = item.actual_value
                setting.updated_by = updated_by_user_id
                setting.updated_on = datetime.now(timezone.utc)

            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to bulk update settings for category_id=%s", setting_category_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update settings."
            )

        logger.info("Bulk update completed for category_id=%s", setting_category_id)
        return list(settings_map.values())
