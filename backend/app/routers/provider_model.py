"""Provider model routes.

Endpoints to list provider models, fetch by ID, bulk update, and list
models for a provider.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.services.provider_service import ProviderService
from app.middleware.auth_middleware import auth_required
from app.schemas.provider_model_schema import ProviderModelResponse, ProviderModelUpdateRequest, ProviderModelUpdateResponse, ProviderModelsByProviderResponse
from shared_orm.models.user import User

router = APIRouter(prefix="/providerModel", tags=["ProviderModel"])
provider_service = ProviderService()

#-------------------------------
# Get All Provider Models
#-------------------------------
@router.get(
    "",
    response_model=list[ProviderModelResponse],
    summary="Get All Provider Models",
    description="Retrieve a list of all provider models."
)
def get_all_provider_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Return a list of all provider models."""

    return provider_service.get_all_providers_models(db=db)

#-------------------------------
# Get Provider Model By ID
#-------------------------------
@router.get(
    "/{model_id}",
    response_model=ProviderModelResponse,
    summary="Get provider model by ID",
    description="Retrieve a specific provider model using its ID."
)
def get_provider_model_by_id(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Get a provider model by its `model_id`."""

    return provider_service.get_provider_model_by_id(
        db=db,
        model_id=model_id
    )

#-------------------------------
# Update Provider Model Bulk
#-------------------------------
@router.put(
    "/providers/{provider_id}/provider-models",
    response_model=list[ProviderModelUpdateResponse],
    summary="Bulk update provider models",
    description="Update multiple provider models for a provider"
)
def update_provider_models(
    provider_id: int,
    payload: list[ProviderModelUpdateRequest],
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    """Bulk update provider models for a provider.

    Accepts a list of model update requests and returns updated items.
    """

    return provider_service.update_provider_models(
        provider_id=provider_id,
        payload=payload,
        updated_by=current_user.id,
        db=db
    )


@router.get(
    "/providers/{provider_id}/models",
    response_model=ProviderModelsByProviderResponse,
    summary="Get Provider Models by Provider ID",
    description="Fetch all model configurations associated with a provider"
)
def get_provider_models_by_provider_id(
    provider_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    """Return model configurations for a given provider ID."""

    return provider_service.get_provider_models_by_provider_id(
        provider_id=provider_id,
        db=db
    )
