from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.page_schema import PaginatedPageResponse,PageInfoResponse
from app.services.page_service import PageService
from app.middleware.auth_middleware import auth_required
from shared_orm.models.user import User

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
    return page_service.get_page_info(
        page_id=page_id,
        site_id=site_id,
        db=db,
        user=user
    )



