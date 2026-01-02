from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.site_schema import (
    SiteCreate,
    SiteUpdate,
    SiteResponse,
    PaginatedSiteResponse
)
from app.services.site_service import SiteService
from app.middleware.auth_middleware import auth_required
from app.models.user import User

router = APIRouter(prefix="/sites", tags=["Sites"])
site_service = SiteService()


@router.post(
    "",
    response_model=SiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new site",
    description="Create a new site for the authenticated user."
)
def create_site(
    data: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """
    Creates a new site.

    - **name**: Site name
    - **url**: Site URL
    - **description**: Optional description

    Only authenticated users can create sites.
    """
    return site_service.create_site(data, db, current_user)


@router.get(
    "",
    response_model=PaginatedSiteResponse,
    summary="Get list of sites",
    description="Retrieve a paginated list of sites belonging to the authenticated user."
)
def get_sites(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page"),
    search: str | None = Query(None, description="Search sites by name"),
    sort: str = Query("created_desc",enum=["created_desc", "created_asc", "title_asc", "title_desc"],description="Sort order"),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """
    Returns paginated sites.

    Supports:
    - Pagination
    - Search
    - Sorting (asc / desc)
    """
    total, sites = site_service.get_sites(db, page, limit, search, sort, current_user)
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": sites
    }


@router.get(
    "/{site_id}",
    response_model=SiteResponse,
    summary="Get site by ID",
    description="Retrieve details of a specific site by its ID."
)
def get_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """
    Fetch a single site.

    - **site_id**: ID of the site
    """
    return site_service.get_site_by_id(site_id, db, current_user)


@router.put(
    "/{site_id}",
    response_model=SiteResponse,
    summary="Update site",
    description="Update an existing site by its ID."
)
def update_site(
    site_id: int,
    data: SiteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """
    Update site details.

    - **site_id**: ID of the site
    - Only provided fields will be updated
    """
    return site_service.update_site(site_id, data, db, current_user)


@router.delete(
    "/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete site",
    description="Delete a site by its ID."
)
def delete_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required)
):
    """
    Permanently deletes a site.

    - **site_id**: ID of the site
    """
    site_service.delete_site(site_id, db, current_user)


@router.post(
    "/analyse/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Analyse site",
    description="Trigger analysis for a site (background processing)."
)
async def analyse_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_required),
):
    """
    Starts analysis for the given site.

    - **site_id**: ID of the site
    - Runs asynchronously
    """
    await site_service.analyse_site(site_id, db, current_user)
