from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc

from shared_orm.models.page import Page
from shared_orm.models.site import Site
from shared_orm.models.user import User
from sqlalchemy import func
from shared_orm.models.test_case import TestCase
from shared_orm.models.test_scenario import TestScenario
from app.schemas.page_schema import PageInfoResponse


class PageService:

    # -------------------------------
    # Pages WITHOUT site
    # -------------------------------
    def list_unlinked_pages(
        self,
        db: Session,
        page: int,
        limit: int,
        search: str | None,
        sort: str,
        user: User
    ):
        query = db.query(Page).filter(Page.site_id.is_(None))

        if search:
            query = query.filter(
                or_(
                    Page.page_title.ilike(f"%{search}%"),
                    Page.page_url.ilike(f"%{search}%")
                )
            )

        if sort == "created_desc":
            query = query.order_by(desc(Page.created_on))
        elif sort == "created_asc":
            query = query.order_by(asc(Page.created_on))
        elif sort == "title_desc":
            query = query.order_by(desc(Page.page_title))
        else:
            query = query.order_by(asc(Page.page_title))

        total = query.count()
        pages = query.offset((page - 1) * limit).limit(limit).all()

        return total, pages

    # -------------------------------
    # Pages UNDER site
    # -------------------------------
    def get_pages_by_site(
        self,
        site_id: int,
        db: Session,
        page: int,
        limit: int,
        search: str | None,
        sort: str,
        user: User
    ):
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found"
            )

        query = db.query(Page).filter(Page.site_id == site_id)

        if search:
            query = query.filter(
                or_(
                    Page.page_title.ilike(f"%{search}%"),
                    Page.page_url.ilike(f"%{search}%")
                )
            )

        if sort == "created_desc":
            query = query.order_by(desc(Page.created_on))
        elif sort == "created_asc":
            query = query.order_by(asc(Page.created_on))
        elif sort == "title_desc":
            query = query.order_by(desc(Page.page_title))
        else:
            query = query.order_by(asc(Page.page_title))

        total = query.count()
        pages = query.offset((page - 1) * limit).limit(limit).all()

        return total, pages
    def get_page_info(
        self,
        page_id: int,
        db: Session,
        user: User,
        site_id: int | None = None
    ) -> PageInfoResponse:

        
        if not page_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page_id is required"
            )

        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found"
            )

        if site_id is not None:
            if page.site_id != site_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Page does not belong to the given site"
                )
                
        else:
            if page.site_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This page is already linked to a site and is not a normal page"
                )

        test_scenario_count = db.query(func.count(TestScenario.id)) \
            .filter(TestScenario.page_id == page.id) \
            .scalar()

        test_case_count = db.query(func.count(TestCase.id)) \
            .filter(TestCase.page_id == page.id) \
            .scalar()

        scheduled_test_case_count = 0

        return PageInfoResponse(
            page_id=page.id,
            page_title=page.page_title,
            status=page.status,
            page_url=page.page_url,
            created_on=page.created_on,
            updated_on=page.updated_on,
            test_scenario_count=test_scenario_count or 0,
            test_case_count=test_case_count or 0,
            scheduled_test_case_count=scheduled_test_case_count
        )
