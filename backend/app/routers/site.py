from fastapi import APIRouter, Depends, Query, status, Response
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.site_schema import (
    SiteCreate,
    SiteUpdate,
    SiteResponse,
    PaginatedSiteResponse,
    SiteInfoResponse
)
from app.services.site_service import SiteService
from app.services.page_service import PageService
from app.middleware.auth_middleware import auth_required
from app.schemas.page_schema import PaginatedPageResponse
from shared_orm.models.user import User

router = APIRouter(prefix="/sites", tags=["Sites"])
site_service = SiteService()
page_service  =PageService()



@router.post(
    "",
    response_model=SiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new site",
    description="Create a new site for the authenticated user."
)
async def create_site(
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
    return await site_service.create_site(data, db, current_user)


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
    return Response(status_code=status.HTTP_204_NO_CONTENT)

    
@router.get(
    "/{site_id}/pages",
    response_model=PaginatedPageResponse,
    summary="Get pages for a site",
    description="Retrieve pages linked to a specific site."
)
def get_pages_by_site(
    site_id: int,
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
    total, pages = page_service.get_pages_by_site(
        site_id=site_id,
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

@router.get("/{site_id}/info", response_model=SiteInfoResponse)
def get_site_info(
    site_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(auth_required)
):
    return site_service.get_site_info(site_id, db, user)


