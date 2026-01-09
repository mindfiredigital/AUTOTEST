from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc

from shared_orm.models.page import Page
from shared_orm.models.site import Site
from shared_orm.models.user import User


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
