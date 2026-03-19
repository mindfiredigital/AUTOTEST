"""Function-related API routes.

Includes endpoints to list functions, fetch a function-provider-model
prompt by IDs, and upsert prompts for function/provider/model mappings.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.middleware.auth_middleware import auth_required
from app.schemas.function_schema import FunctionProviderModelResponse,FunctionProviderModelUpsertRequest
from app.services.function_service import FunctionService
from shared_orm.models.user import User

router = APIRouter(prefix="/functions", tags=["Functions"])
function_service = FunctionService()

#-------------------------------
# Get All Providers
#-------------------------------
@router.get(
    "/all",
    summary="Get all functions",
    description="Retrieve a list of all functions."
)
def get_all_functions(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Return a list of all functions."""
    return function_service.get_all_functions(db=db)


#-------------------------------
# Get Prompt By Function ID, API Provider ID, and Model ID
#-------------------------------
@router.get(
    "/{function_id}/{provider_id}/{model_id}",
    # response_model=FunctionProviderModelResponse,
    summary="Get prompt by function provider model by IDs",
    description="Retrieve a specific function provider model using its IDs."
)
def get_function_provider_model_by_ids(
    function_id: int,
    provider_id: int,
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Get a function-provider-model mapping by IDs."""

    return function_service.get_function_provider_model_by_ids(
        function_id=function_id,
        provider_id=provider_id,
        model_id=model_id,
        db=db
    )

#-------------------------------
# Update Prompt by Function ID, API Provider ID, and Model ID
#-------------------------------
@router.put(
    "/function-provider-model",
    response_model=FunctionProviderModelResponse,
    summary="Create or update function provider model prompt",
    description="Upsert prompt for a function-provider-model mapping."
)
def upsert_function_provider_model_prompt(
    payload: FunctionProviderModelUpsertRequest,   
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    """Create or update the prompt for a function-provider-model."""

    return function_service.update_function_provider_model_prompt_by_ids(
        function_id=payload.function_id,
        provider_id=payload.provider_id,
        model_id=payload.provider_model_id,
        additional_info=payload.additional_info,
        db=db,
        current_user=current_user,
    )

