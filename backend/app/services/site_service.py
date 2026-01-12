import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc
from fastapi import HTTPException, status
from datetime import datetime
from sqlalchemy import func
from shared_orm.models.site import Site
from app.schemas.site_schema import SiteCreate, SiteUpdate,SiteInfoResponse
from shared_orm.models.user import User
from app.messaging.rabbitmq_producer import rabbitmq_producer
from app.config.setting import settings
from app.config.logger import logger
from shared_orm.models.test_scenario import TestScenario
from shared_orm.models.test_case import TestCase
from shared_orm.models.test_suite import TestSuite
from shared_orm.models.page import Page


class SiteService:

    async def create_site(self, data: SiteCreate, db: Session, user: User) -> Site:
        existing = db.query(Site).filter(Site.site_url == data.site_url).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Site URL already exists"
            )

        site = Site(
            site_title=data.site_title,
            status ="New",
            site_url=str(data.site_url),
            created_on=datetime.utcnow(),
            created_by= user.id
        )

        db.add(site)
        db.commit()
        db.refresh(site)
        message = {
            "event": "PAGE_EXTRACT",
            "site_id": site.id,
            "site_url": site.site_url,
            "requested_by": user.id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        asyncio.create_task(
            rabbitmq_producer.publish_message(
                queue_name=settings.PAGE_EXTRACT_QUEUE,
                message=message,
                priority=5,
            )
        )
        return site

    def get_sites(
        self,
        db: Session,
        page: int,
        limit: int,
        search: str | None,
        sort: str,
        user: User
    ):
        query = db.query(Site)

        if search:
            query = query.filter(
                or_(
                    Site.site_title.ilike(f"%{search}%"),
                    Site.site_url.ilike(f"%{search}%")
                )
            )

        # Sorting
        if sort == "created_desc":
            query = query.order_by(desc(Site.created_on))
        elif sort == "created_asc":
            query = query.order_by(asc(Site.created_on))
        elif sort == "title_desc":
            query = query.order_by(desc(Site.site_title))
        else:
            query = query.order_by(asc(Site.site_title))

        total = query.count()

        sites = (
            query
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        return total, sites

    def get_site_by_id(self, site_id: int, db: Session, user: User) -> Site:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found"
            )
        return site

    def update_site(self, site_id: int, data: SiteUpdate, db: Session, user: User) -> Site:
        site = self.get_site_by_id(site_id, db)

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(site, field, value)

        site.updated_on = datetime.utcnow()
        db.commit()
        db.refresh(site)
        return site

    def delete_site(self, site_id: int, db: Session, user: User):
        site = self.get_site_by_id(site_id, db)
        db.delete(site)
        db.commit()

    def get_site_info(self, site_id: int, db: Session, user: User) -> SiteInfoResponse:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Site not found"
            )
        page_count = db.query(func.count(Page.id)) \
            .filter(Page.site_id == site_id) \
            .scalar()

        test_scenario_count = db.query(func.count(TestScenario.id)) \
            .join(Page, TestScenario.page_id == Page.id) \
            .filter(Page.site_id == site_id) \
            .scalar()

        test_case_count = db.query(func.count(TestCase.id)) \
            .join(Page, TestCase.page_id == Page.id) \
            .filter(Page.site_id == site_id) \
            .scalar()

        test_suite_count = db.query(func.count(TestSuite.id)) \
            .filter(TestSuite.site_id == site_id) \
            .scalar()

        return SiteInfoResponse(
            site_id=site.id,
            site_title=site.site_title,
            site_url=site.site_url,
            status=site.status,
            created_on=site.created_on,
            updated_on=site.updated_on,
            page_count=page_count or 0,
            test_scenario_count=test_scenario_count or 0,
            test_case_count=test_case_count or 0,
            test_suite_count=test_suite_count or 0,
            test_environment=None,          
            scheduled_test_cases=None      
        )
        
    