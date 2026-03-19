from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, asc, desc
from shared_orm.models.page import Page
from shared_orm.models.site import Site
from shared_orm.models.user import User
from sqlalchemy import func
from shared_orm.models.test_case import TestCase
from shared_orm.models.test_scenario import TestScenario
from shared_orm.models.page_link import PageLink
from shared_orm.models.test_execution import TestExecution
from app.schemas.page_schema import PageInfoResponse
from app.config.logger import logger
from app.config.setting import settings
import asyncio
from app.messaging.rabbitmq_producer import rabbitmq_producer


class PageService:

    async def create_page(
        self,
        page_title: str | None,
        page_url: str,
        db: Session,
        user: User
    ):
        logger.info(f"[CREATE_PAGE_REQUEST] User={user.id} URL={page_url}")
        if not page_url or not page_url.strip():
            logger.warning("[CREATE_PAGE_FAILED] Empty page_url")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page URL is required"
            )
        new_page = Page(
            page_title=page_title.strip() if page_title else None,
            page_url=page_url.strip(),
            site_id=None,
            status="new",
            created_on=datetime.now(timezone.utc),
            created_by=user.id,
            updated_on=None,
            updated_by=None,
            page_source=None,
            page_metadata=None
        )
        db.add(new_page)
        db.commit()
        db.refresh(new_page)
        logger.info(f"[CREATE_PAGE_SUCCESS] PageID={new_page.id}")
        message = {
            "event": "PAGE_EXTRACT_SINGLE",
            "site_id": new_page.site_id,
            "extract_url": new_page.page_url,
            "page_id": new_page.id,
            "requested_by": user.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        asyncio.create_task(
            rabbitmq_producer.publish_message(
                queue_name=settings.PAGE_EXTRACT_SINGLE_QUEUE,
                message=message,
                priority=5,
            )
        )
        logger.info(
            f"[PAGE_EXTRACT_SINGLE_PUBLISHED] PageID={new_page.id} "
            f"Queue={settings.PAGE_EXTRACT_SINGLE_QUEUE}"
        )
        return new_page

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
        logger.info(
            f"[LIST_UNLINKED_PAGES] User={user.id} Page={page} "
            f"Limit={limit} Search={search} Sort={sort}"
        )
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
        logger.info(f"[LIST_UNLINKED_PAGES_SUCCESS] Total={total}")
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
            logger.warning(
                f"[GET_PAGES_BY_SITE_FAILED] Site not found | SiteID={site_id}"
            )
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
        logger.info(f"[GET_PAGES_BY_SITE_SUCCESS] SiteID={site_id} Total={total}")
        return total, pages

    def get_page_info(
        self,
        page_id: int,
        db: Session,
        user: User,
        site_id: int | None = None
    ) -> PageInfoResponse:
        logger.info(
            f"[GET_PAGE_INFO] User={user.id} PageID={page_id} SiteID={site_id}"
        )
        if not page_id:
            logger.warning("[GET_PAGE_INFO_FAILED] page_id missing")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="page_id is required"
            )

        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            logger.warning(
                f"[GET_PAGE_INFO_FAILED] Page not found | PageID={page_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found"
            )

        if site_id is not None:
            if page.site_id != site_id:
                logger.warning(
                    f"[GET_PAGE_INFO_FAILED] Page does not belong to site | PageID={page_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Page does not belong to the given site"
                )

        test_scenario_count = db.query(func.count(TestScenario.id)) \
            .filter(TestScenario.page_id == page.id) \
            .scalar()

        test_case_count = db.query(func.count(TestCase.id)) \
            .filter(TestCase.page_id == page.id) \
            .scalar()

        scheduled_test_case_count = 0
        logger.info(f"[GET_PAGE_INFO_SUCCESS] PageID={page_id}")

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

    def delete_page(self, page_id: int, db: Session, user: User):
        logger.info(f"[DELETE_PAGE_REQUEST] User={user.id} PageID={page_id}")

        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            logger.warning(
                f"[DELETE_PAGE_FAILED] Page not found | PageID={page_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found"
            )

        db.query(TestCase).filter(
            TestCase.page_id == page.id
        ).delete(synchronize_session=False)
        db.query(TestScenario).filter(
            TestScenario.page_id == page.id
        ).delete(synchronize_session=False)
        db.query(TestExecution).filter(
            TestExecution.page_id == page.id
        ).delete(synchronize_session=False)
        db.query(PageLink).filter(
            or_(
                PageLink.page_id_source == page.id,
                PageLink.page_id_target == page.id
            )
        ).delete(synchronize_session=False)
        db.delete(page)
        db.commit()
        logger.info(f"[DELETE_PAGE_SUCCESS] PageID={page_id} Deleted successfully")

    def update_page_title(
        self,
        page_id: int,
        new_title: str,
        db: Session,
        user: User
    ):
        logger.info(
            f"[UPDATE_PAGE_TITLE_REQUEST] User={user.id} PageID={page_id}"
        )
        if not new_title or not new_title.strip():
            logger.warning(
                f"[UPDATE_PAGE_TITLE_FAILED] Empty title | PageID={page_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page title cannot be empty"
            )
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            logger.warning(
                f"[UPDATE_PAGE_TITLE_FAILED] Page not found | PageID={page_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found"
            )
        old_title = page.page_title
        page.page_title = new_title.strip()
        page.updated_on = datetime.now(timezone.utc)
        page.updated_by = user.id
        db.commit()
        db.refresh(page)
        logger.info(
            f"[UPDATE_PAGE_TITLE_SUCCESS] PageID={page_id} "
            f"OldTitle='{old_title}' NewTitle='{page.page_title}'"
        )
        return page

    # -------------------------------------------------------------------------
    # AUTH CREDENTIAL UPDATE
    # -------------------------------------------------------------------------
    # IMPORTANT: This method is async because it awaits rabbitmq_producer.
    # The router endpoint MUST also be `async def` — using asyncio.run() from
    # a sync context creates a NEW event loop which conflicts with the
    # rabbitmq_producer connection that was established on the FastAPI loop,
    # causing the "Future attached to a different loop" error.
    # -------------------------------------------------------------------------

    async def auth_credential_update(
        self,
        page_id: int,
        db: Session,
        user: User,
    ):
        logger.info(
            f"[PROCESS_AUTH_UPDATE] User={user.id} PageID={page_id}"
        )

        # locate a canonical login test case for this page
        testcase = (
            db.query(TestCase)
            .join(TestScenario, TestScenario.id == TestCase.test_scenario_id)
            .filter(
                TestCase.page_id == page_id,
                TestCase.is_valid == True,
                TestCase.is_valid_default == True,
                TestScenario.requires_auth == True,
            )
            .first()
        )

        if not testcase:
            logger.warning(
                f"[PROCESS_AUTH_UPDATE] No login test case found | PageID={page_id}"
            )
            return {"message": "Auth credentials updated, but no login test case found."}

        # publish an event with only identifiers; worker will perform login

        message = {
            "event": "AUTH_CREDENTIAL_UPDATE",
            "test_case_id": testcase.id,
            "requested_by": user.id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await rabbitmq_producer.publish_message(
            settings.AUTH_CREDENTIAL_UPDATE_QUEUE,
            message,
            priority=6,
        )

        return {"message": "Auth credentials updated and login re-validation triggered."}
