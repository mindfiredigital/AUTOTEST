"""Provider routes: list, update, and retrieve provider data."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.services.provider_service import ProviderService
from app.middleware.auth_middleware import auth_required
from app.schemas.provider_schema import ProviderResponse,ActiveProviderResponse,ProviderModelMinimalResponse
from shared_orm.models.user import User
from typing import List
from app.schemas.provider_schema import ProviderBulkUpdate

router = APIRouter(prefix="/providers", tags=["Providers"])
provider_service = ProviderService()

#-------------------------------
# Get All Providers
#-------------------------------
@router.get(
    "",
    response_model=list[ProviderResponse],
    summary="Get all providers",
    description="Retrieve a list of all providers."
)
def get_all_providers(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Return a list of all providers."""

    return provider_service.get_all_providers(db=db)

@router.put(
    "/bulk-update",
    response_model=list[ProviderResponse],
    summary="Bulk update providers",
    description="Bulk update multiple providers at once."
)
def bulk_update_providers(
    payload: list[ProviderBulkUpdate],
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    """Bulk update multiple providers and return updated items."""

    return provider_service.bulk_update_providers(
        payload=payload,
        db=db,
        current_user=current_user,
    )

@router.get(
    "/active",
    response_model=list[ActiveProviderResponse],
    summary="Get active providers",
    description="Retrieve all active providers (id and title only)."
)
def get_active_providers(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    """Return a minimal list of active providers (id and title)."""

    return provider_service.get_active_providers(
        db=db,
        current_user=current_user
    )

@router.get(
    "/{provider_id}/models",
    response_model=list[ProviderModelMinimalResponse],
    summary="Get provider models by provider id",
    description="Retrieve provider models (id and model only) for a provider."
)
def get_provider_models_minimal(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    """Return minimal model info for a given provider ID."""

    return provider_service.get_models_by_provider_id(
        provider_id=provider_id,
        db=db,
        current_user=current_user
    )


#-------------------------------
# Get Providers By ID
#-------------------------------
@router.get(
    "/{provider_id}",
    response_model=ProviderResponse,
    summary="Get provider by ID",
    description="Retrieve a specific provider using its ID."
)
def get_provider_by_id(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Retrieve a provider by its `provider_id`."""

    return provider_service.get_provider_by_id(
        provider_id=provider_id,
        db=db
    )

#-------------------------------
# Update Provider
#-------------------------------
@router.put(
    "/{provider_id}",
    response_model=ProviderResponse,
    summary="Update provider",
    description="Update the details of a specific provider."
)
def update_provider(
    provider_id: int,
    key: str,
    is_active: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Update provider attributes such as `key` and `is_active`."""

    return provider_service.update_provider(
        provider_id=provider_id,
        key=key,
        is_active=is_active,
        db=db
    )

