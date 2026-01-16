from datetime import datetime
from urllib.parse import urlparse

from app.config.logger import logger
from app.services.selenium_driver import get_driver
from app.extractor.url_extractor import URLExtractor
from app.config.setting import settings
from app.services.page_analysis_service import PageAnalysisService
from app.llm.llm_wrapper import LLMWrapper
from app.llm.prompt_manager import PromptManager
from app.config.setting import settings
from app.messaging.rabbitmq_producer import rabbitmq_producer

from shared_orm.models.site import Site
from shared_orm.models.page import Page
from shared_orm.models.site_alias import SiteAlias
from app.config.database import SessionLocal


class WorkerService:
    
    async def process_page_extract(self, body: dict):
        """
        Handles PAGE_EXTRACT_QUEUE
        Extracts pages and updates DB
        """
        logger.info(f"[PAGE_EXTRACT] Started | payload={body}")

        site_id = body.get("site_id")
        site_url = body.get("site_url")
        requested_by = body.get("requested_by")

        if not site_id or not site_url:
            raise ValueError("site_id or site_url missing")

        db = SessionLocal()

        try:
            site = db.query(Site).filter(Site.id == site_id).first()
            if not site:
                logger.warning("Site not found")
                return

            if site.status == "Pause":
                logger.info("Site paused before extraction")
                return

            site.status = "Processing"
            site.updated_on = datetime.utcnow()
            site.updated_by = requested_by
            db.commit()

            driver = get_driver()
            extractor = URLExtractor(driver, logger)

            try:
                urls = extractor.extract_urls(site_url)
                base_domain = urlparse(site_url).netloc

                for url in urls:
                    db.refresh(site)
                    if site.status == "Pause":
                        logger.info("Site paused during extraction")
                        return

                    exists = db.query(Page).filter(Page.page_url == url).first()
                    if not exists:
                        db.add(
                            Page(
                                site_id=site.id,
                                page_url=url,
                                status="New",
                                created_on=datetime.utcnow(),
                                created_by=requested_by,
                            )
                        )

                    parsed = urlparse(url)
                    if parsed.netloc != base_domain:
                        alias_exists = db.query(SiteAlias).filter(
                            SiteAlias.site_id == site.id,
                            SiteAlias.site_alias_url == parsed.netloc
                        ).first()

                        if not alias_exists:
                            db.add(
                                SiteAlias(
                                    site_id=site.id,
                                    site_alias_url=parsed.netloc
                                )
                            )

                db.commit()

                site.status = "Done"
                site.updated_on = datetime.utcnow()
                db.commit()

                logger.info(f"[PAGE_EXTRACT] Completed | site_id={site.id}")

                # emiting the PAGE_ANALYSE event
                # message = {
                #     "event": "PAGE_ANALYSE",
                #     "site_id": site.id,
                #     "requested_by": requested_by,
                #     "timestamp": datetime.utcnow().isoformat(),
                # }

                # await rabbitmq_producer.publish_message(
                #     queue_name=settings.PAGE_ANALYSE_QUEUE,
                #     message=message,
                #     priority=5,
                # )

            finally:
                driver.quit()

        except Exception as e:
            logger.exception(f"[PAGE_EXTRACT] Failed | error={e}")
            raise

        finally:
            db.close()

    
    async def process_page_analyse(self, body: dict):
        """
        Handles PAGE_ANALYSE_QUEUE
        Extracts pages and updates DB
        """
        logger.info(f"[PAGE_ANALYSE_QUEUE] Started | payload={body}")

        site_id = body.get("site_id")
        requested_by = body.get("requested_by")

        db = SessionLocal()
        driver = get_driver()

        llm = LLMWrapper()
        prompt_manager = PromptManager()

        analyzer = PageAnalysisService(
            driver=driver,
            logger=logger,
            llm=llm,
            prompt_manager=prompt_manager
        )
        
        try:
            while True:
                page = (
                    db.query(Page)
                    .filter(Page.site_id == site_id, Page.status == "new")
                    .with_for_update(skip_locked=True)
                    .first()
                )

                if not page:
                    break

                page.status = "generating_metadata"
                db.commit()

                try:
                    analyzer.analyze_page(
                        page_id=page.id,
                        page_url=page.page_url,
                        requested_by=requested_by
                    )
                    page.status = "generating_metadata"
                    db.commit()

                except Exception:
                    page.status = "new"
                    db.commit()

        finally:
            driver.quit()
            db.close()

worker_service = WorkerService()