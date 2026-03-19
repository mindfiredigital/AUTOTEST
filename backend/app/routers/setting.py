"""Settings management routes.

Endpoints to list categories, retrieve settings, and update actual
values individually or in bulk.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.services.setting_service import SettingService
from app.middleware.auth_middleware import auth_required
from app.schemas.setting_schema import BulkSettingUpdateRequest, SettingResponse, SettingUpdateActualValue
from shared_orm.models.user import User

router = APIRouter(prefix="/settings", tags=["Settings"])
setting_service = SettingService()

# -------------------------------
# Setting Categories
# -------------------------------
@router.get(
    "/categories",
    summary="Get all setting categories",
    description="Retrieve all available setting categories."
)
def get_all_setting_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Return all available setting categories."""

    return setting_service.get_all_setting_categories(db=db)

# -------------------------------
# Setting Category by ID
# -------------------------------
@router.get(
    "/categories/{category_id}",
    summary="Get setting category by ID",
    description="Retrieve a specific setting category using its ID."
)
def get_setting_category_by_id(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Retrieve a setting category by its ID."""

    return setting_service.get_setting_category_by_id(
        setting_category_id=category_id,
        db=db
    )

# -------------------------------
# Settings by Category
# -------------------------------
@router.get(
    "",
    summary="Get all settings",
    description="Retrieve all settings."
)
def get_all_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Return all settings across categories."""

    return setting_service.get_all_settings(db=db)

# -------------------------------
# Setting by ID
# -------------------------------
@router.get(
    "/{setting_id}",
    summary="Get setting by ID",
    description="Retrieve a specific setting using its ID."
)
def get_setting_by_id(
    setting_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Retrieve a specific setting by its ID."""

    return setting_service.get_setting_by_id(
        setting_id=setting_id,
        db=db
    )

# -------------------------------
# Settings by Category ID
# -------------------------------
@router.get(
    "/category/{setting_category_id}",
    summary="Get settings by category",
    description="Retrieve all settings under a specific category."
)
def get_settings_by_category(
    setting_category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Return settings belonging to a given category ID."""

    return setting_service.get_setting_by_category(
        setting_category_id=setting_category_id,
        db=db
    )
# -------------------------------
# Update Setting Actual Value
# -------------------------------
@router.put("/{setting_id}/actual-value", response_model=None)
def update_setting_actual_value(
    setting_id: int,
    payload: SettingUpdateActualValue,
    db: Session = Depends(get_db),
):
    """Update the actual value for a single setting."""

    return setting_service.update_actual_value(
        setting_id=setting_id,
        actual_value=payload.actual_value,
        db=db
    )

@router.patch(
    "/category/{setting_category_id}/actual-values",
    response_model=list[SettingResponse]

)
def update_settings_by_category(
    setting_category_id: int,
    request: BulkSettingUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Bulk update actual values for all settings in a category."""

    return setting_service.update_actual_values_by_category(
        setting_category_id=setting_category_id,
        updates=request.settings,
        db=db,
        updated_by_user_id=current_user.id
    )