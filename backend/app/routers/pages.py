"""Page management routes.

Endpoints for listing, creating, updating, and deleting pages.
"""

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.page_schema import PaginatedPageResponse,PageInfoResponse, PageUpdateTitleRequest, PageCreateRequest
from app.services.page_service import PageService
from app.middleware.auth_middleware import auth_required
from shared_orm.models.user import User
from app.config.logger import logger
from datetime import datetime, timezone

router = APIRouter(prefix="/pages", tags=["Pages"])
page_service = PageService()

# -------------------------------
# Pages WITHOUT site
# -------------------------------
@router.get(
    "/unlinked",
    response_model=PaginatedPageResponse,
    summary="Get pages without site",
    description="Retrieve pages that are not linked to any site."
)
def list_unlinked_pages(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    sort: str = Query(
        "created_desc",
        enum=["created_desc", "created_asc", "title_asc", "title_desc"]
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Return paginated pages that are not linked to a site."""

    total, pages = page_service.list_unlinked_pages(
        db=db,
        page=page,
        limit=limit,
        search=search,
        sort=sort,
        user=current_user
    )

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": pages
    }

@router.get("/info", response_model=PageInfoResponse)
def get_page_info(
    page_id: int,
    site_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(auth_required)
):
    """Return detailed information for a page (optionally scoped to a site)."""

    return page_service.get_page_info(
        page_id=page_id,
        site_id=site_id,
        db=db,
        user=user
    )

@router.delete(
    "/{page_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a page",
    description="Permanently deletes a page and all linked test scenarios, test cases, and navigation data."
)
def delete_page(
    page_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Permanently delete a page and any linked test data."""

    page_service.delete_page(
        page_id=page_id,
        db=db,
        user=current_user
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.patch(
    "/{page_id}/title",
    summary="Update page title",
    description="Update the title of a page"
)
def update_page_title(
    page_id: int,
    payload: PageUpdateTitleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Update the title of an existing page."""

    return page_service.update_page_title(
        page_id=page_id,
        new_title=payload.page_title,
        db=db,
        user=current_user
    )

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Create new unlinked page"
)
async def create_page(
    payload: PageCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """Create a new unlinked page and return its representation."""

    return await page_service.create_page(
        page_title=payload.page_title,
        page_url=payload.page_url,
        db=db,
        user=current_user
    )
        
@router.post(
    "/process-auth-update",
    summary="Process auth credential update for pages",
)
async def auth_credential_update(           # ← must be async def
    page_id: int = Query(..., description="ID of the site for which auth credentials were updated"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    """Process an auth credential update for pages and refresh state."""

    result = await page_service.auth_credential_update(   # ← await
        page_id=page_id,
        db=db,
        user=current_user,
    )
    return result
