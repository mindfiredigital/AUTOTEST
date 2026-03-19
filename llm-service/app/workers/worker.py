"""
PIPELINE FLOW
=============

  PAGE_EXTRACT
      │  page.status → "new"
      ▼
  PAGE_ANALYSE                        page.status → "generating_metadata"
      │
      ▼
  TEST_SCENARIO_GENERATE              page.status → "generating_test_scenarios"
      │
      ▼
  TEST_CASE_GENERATE                  page.status → "generating_test_cases"
      │
      ├── AUTH CHECK → LOGIN → PAGE_EXTRACT_SINGLE (new URLs only)
      │                              │
      │                              └─► PAGE_ANALYSE → TEST_SCENARIO
      │                                  → TEST_CASE  (loops for new pages)
      ▼
  TEST_SCRIPT_GENERATE                page.status → "generating_test_scripts"
      │   script saved to scenario.script / scenario.script_path
      ▼
  TEST_EXECUTION (blank)              page.status → "done"

──────────────────────────────────────────────────────────────────
PAUSE / RESUME  (site-level flag only)
──────────────────────────────────────────────────────────────────
  Pause:
    • API sets site.status = "Paused"
    • Every pipeline step checks _is_paused(site_id) at entry.
      If paused → return early (page keeps its current status so
      resume knows exactly where to restart from).

  Resume:
    • API sets site.status = "Processing" then publishes
      event=SITE_RESUME with site_id.
    • process_resume() scans all non-done pages for that site
      and re-emits the correct queue message per page.status:

        "new"  / "generating_metadata"       → PAGE_ANALYSE
        "generating_test_scenarios"           → TEST_SCENARIO_GENERATE
        "generating_test_cases"               → TEST_CASE_GENERATE
        "generating_test_scripts"             → TEST_SCRIPT_GENERATE
        "done"                                → skipped

──────────────────────────────────────────────────────────────────
WEBSOCKET — page status broadcast
──────────────────────────────────────────────────────────────────
  Every page.status change calls _notify_ws() which sends a
  PAGE_STATUS_UPDATE message to the connected user (requested_by).

──────────────────────────────────────────────────────────────────
AUTH CREDENTIAL UPDATE  (separate entry point)
──────────────────────────────────────────────────────────────────
  process_auth_credential_update():
    • Triggered from frontend when user changes login credentials.
    • Resolves new credentials, drives Selenium to login, captures
      landing URL, then emits PAGE_EXTRACT_SINGLE for that URL.
    • New pages flow through the full pipeline independently.

──────────────────────────────────────────────────────────────────
SCENARIO RE-RUN  (targeted, single scenario)
──────────────────────────────────────────────────────────────────
  process_scenario_rerun():
    • Frontend triggers re-run for one specific scenario.
    • Sets page.status = "generating_test_cases".
    • Emits TEST_CASE_GENERATE with scenario_id so only that
      scenario's test cases + script are regenerated.

──────────────────────────────────────────────────────────────────
ANTI-LOOP GUARANTEE
──────────────────────────────────────────────────────────────────
  • PAGE_EXTRACT_SINGLE inserts only URLs absent from Page table.
  • process_page_analyse early-returns when page.status != "new".
  • _perform_login_and_discover checks landing URL before emitting.
"""

from datetime import datetime
from urllib.parse import urlparse
import asyncio

from app.config.logger import logger
from app.services.selenium_driver import get_driver
from app.extractor.url_extractor import URLExtractor
from app.services.page_analysis_service import PageAnalysisService
from app.llm.llm_wrapper import LLMWrapper
from app.llm.prompt_manager import PromptManager
from app.messaging.rabbitmq_producer import rabbitmq_producer
from app.config.database import SessionLocal
from app.config.setting import settings
from app.services.test_scenario_service import TestScenarioService
from app.services.test_case_service import TestCaseService
from app.services.test_credential_service import TestCredentialService
from app.services.test_script_service import TestScriptService
from app.services.test_execution_service import TestExecutionService

from shared_orm.models.site import Site
from shared_orm.models.page import Page
from shared_orm.models.site_alias import SiteAlias
from shared_orm.models.test_scenario import TestScenario
from shared_orm.models.test_case import TestCase


# ─────────────────────────────────────────────────────────────────────────────
# Page status constants — single source of truth
# ─────────────────────────────────────────────────────────────────────────────

class PageStatus:
    NEW                       = "new"
    GENERATING_METADATA       = "generating_metadata"
    GENERATING_TEST_SCENARIOS = "generating_test_scenarios"
    GENERATING_TEST_CASES     = "generating_test_cases"
    GENERATING_TEST_SCRIPTS   = "generating_test_scripts"
    DONE                      = "done"


# Resume map: page.status → (queue, event, priority)
# Pages in "new" or "generating_metadata" both restart at PAGE_ANALYSE
# because metadata may be incomplete if paused mid-analysis.
_RESUME_MAP = {
    PageStatus.NEW:                       (settings.PAGE_ANALYSE_QUEUE,  "PAGE_ANALYSE",          5),
    PageStatus.GENERATING_METADATA:       (settings.PAGE_ANALYSE_QUEUE,  "PAGE_ANALYSE",          5),
    PageStatus.GENERATING_TEST_SCENARIOS: (settings.TEST_SCENARIO_QUEUE, "TEST_SCENARIO_GENERATE",5),
    PageStatus.GENERATING_TEST_CASES:     (settings.TEST_CASE_QUEUE,     "TEST_CASE_GENERATE",    5),
    PageStatus.GENERATING_TEST_SCRIPTS:   (settings.TEST_SCRIPT_QUEUE,   "TEST_SCRIPT_GENERATE",  5),
    # PageStatus.DONE intentionally absent — nothing to resume
}


# ─────────────────────────────────────────────────────────────────────────────

class WorkerService:

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    def _is_paused(self, site_id: int) -> bool:
        """
        Check whether the site is currently paused.
        Opens its own short-lived DB session so it can be called anywhere.
        """
        with SessionLocal() as db:
            site = db.query(Site).filter(Site.id == site_id).first()
            return site is not None and site.status == "Paused"

    def _set_page_status(self, db, page: Page, status: str, requested_by: int):
        """
        Update page.status + audit columns and flush (caller must commit).
        Returns the page so callers can chain if needed.
        """
        page.status     = status
        page.updated_on = datetime.utcnow()
        page.updated_by = requested_by
        db.flush()
        return page

    async def _notify_ws(self, page: Page, requested_by: int,scenario_id: int | None = None):
          
        """
          Publish PAGE_STATUS_UPDATE event to RabbitMQ.

          This method is fire-and-forget.
          Any failure here must NOT break the main processing pipeline.
        """

        try:
              
              db = SessionLocal()
              scenario_count = (db.query(TestScenario).filter(TestScenario.page_id == page.id).count() )
              test_case_count = (db.query(TestCase).filter(TestCase.page_id == page.id).count())

              payload = {
            "page_id": page.id,
            "page_url": page.page_url,
            "site_id": page.site_id,
            "page_title": page.page_title,
            "status": page.status,
            "requested_by": requested_by,
            "test_scenario_count": scenario_count,
            "test_case_count": test_case_count,
            "updated_on": (
                page.updated_on.isoformat()
                if page.updated_on
                else None
            ),
        }
              if scenario_id is not None:
                  logger.info(f"[WS_NOTIFY] Received with  scenario_id = {scenario_id} ")
                  payload["scenario_id"] = scenario_id

              message = {
                "event": "PAGE_STATUS_UPDATE",
                "payload": payload,
                }
              
                   
              await rabbitmq_producer.publish_message(settings.PAGE_STATUS_UPDATE_QUEUE,message)
              logger.info(
                f"[WS_NOTIFY] Published PAGE_STATUS_UPDATE | "
                f"page_id={page.id} | "
                f"status={page.status} | "
                f"scenarios={scenario_count} | "
                f"cases={test_case_count}")
        except Exception as e:
            logger.error(
            f"[WS_NOTIFY] FAILED to publish PAGE_STATUS_UPDATE | "
            f"page_id={page.id} | status={page.status} | error={e}"
        )
        
        finally:
            db.close()

    def _get_login_test_case(self, db, page_id: int):
        """
        Return the single canonical login test case for a page:
          - scenario.requires_auth = True
          - test_case.is_valid = True
          - test_case.is_valid_default = True
        """
        return (
            db.query(TestCase)
            .join(TestScenario, TestScenario.id == TestCase.test_scenario_id)
            .filter(
                TestCase.page_id           == page_id,
                TestCase.is_valid          == True,
                TestCase.is_valid_default  == True,
                TestScenario.requires_auth == True,
            )
            .first()
        )

    def _detect_auth_requirements(self, db, page_id: int) -> bool:
        """
        Scan all scenarios for this page; set requires_auth=True on matching ones.
        Returns True if at least one scenario requires auth.
        """
        scenarios = db.query(TestScenario).filter(
            TestScenario.page_id == page_id
        ).all()

        auth_keywords = [
            "login", "signin", "sign in", "log in", "authenticate",
            "password", "username", "email", "credential",
            "register", "signup", "sign up", "account",
        ]
        auth_selectors = [
            "login", "signin", "password", "username", "email",
            "auth", "credential", "register", "signup",
        ]

        has_auth = False

        for scenario in scenarios:
            requires_auth = False
            title_lower   = (scenario.title or "").lower()

            if any(kw in title_lower for kw in auth_keywords):
                requires_auth = True

            if not requires_auth and scenario.data:
                for step in scenario.data.get("steps", []):
                    if isinstance(step, dict):
                        if any(kw in step.get("action", "").lower() for kw in auth_keywords):
                            requires_auth = True
                        if any(kw in str(step.get("target", "")).lower() for kw in auth_keywords):
                            requires_auth = True

                if any(kw in scenario.data.get("entry_point", "").lower() for kw in auth_keywords):
                    requires_auth = True

                if any(kw in str(scenario.data.get("flow_structure", "")).lower() for kw in auth_selectors):
                    requires_auth = True

            if not requires_auth and scenario.category:
                if "auth" in scenario.category.lower():
                    requires_auth = True

            if requires_auth:
                scenario.requires_auth = True
                has_auth = True
                logger.info(
                    f"[AUTH_DETECT] Scenario '{scenario.title}' "
                    f"(id={scenario.id}) → requires_auth=True"
                )

        db.commit()
        return has_auth

    async def _perform_login_and_discover(self, body: dict):
        """
        1. Resolve credentials for the login test case.
        2. Drive Selenium to log in.
        3. Capture post-auth landing URL.
        4. Save landing URL on the test case record.
        5. Emit PAGE_EXTRACT_SINGLE only if the landing URL is new.
        """
        db = SessionLocal()
        test_case_id = body["test_case_id"]
        requested_by = body["requested_by"]

        test_case = db.query(TestCase).filter(TestCase.id == test_case_id).first()
        if not test_case:
            logger.warning(f"[AUTH] Test case not found | TestCaseID={test_case_id}")
            return

        page = db.query(Page).filter(Page.id == test_case.page_id).first()
        if not page:
            return

        driver         = get_driver()
        llm            = LLMWrapper(db=db)
        prompt_manager = PromptManager()
        cred_service   = TestCredentialService(llm=llm, logger=logger)

    
        try:
            resolved = cred_service.resolve(page.id, test_case.data.get("test_data", {}))

            selectors = test_case.data.get("selectors", {})
            username_selector = selectors.get("username")
            password_selector = selectors.get("password")

            def extract_field(selector):
                """
                 Extract field name from selector.

                Examples:
                #txtName → txtName
                input#user-name → user-name
                input[name="email"] → email
                """
                import re
                if not selector:
                    return None
                if selector.startswith("#"):
                    return selector[1:]
                if "#" in selector:
                    return selector.split("#")[-1]
                match = re.search(r'name=["\']([^"\']+)["\']', selector)
                if match:
                    return match.group(1)
                return None
            username_field = extract_field(username_selector)
            password_field = extract_field(password_selector)
            username = resolved.get(username_field)
            password = resolved.get(password_field)
            if not username or not password:
                logger.warning(
                f"[AUTH] Missing credentials | username_field={username_field}, password_field={password_field}"
            )
                return
                
            driver.get(page.page_url)

            analyzer = PageAnalysisService(
                driver=driver, logger=logger, llm=llm, prompt_manager=prompt_manager
            )
            success = analyzer.login_to_website(username=username, password=password)

            if not success:
                logger.warning("[AUTH] Login failed — skipping post-auth discovery")
                return

            logger.info("[AUTH] Login successful")
            landing_url = driver.current_url

            # Persist landing URL on the test case
            if test_case.expected_outcome is None:
                test_case.expected_outcome = {}
            test_case.expected_outcome["post_auth_landing_url"] = landing_url
            db.commit()

            # ---------------------------------------------
            # Save landing page
            # ---------------------------------------------
            existing_page = db.query(Page).filter(
                Page.site_id == page.site_id,
                Page.page_url == landing_url
            ).first()

            if existing_page:
                landing_page = existing_page
                logger.info(f"[AUTH] Landing page already exists: {landing_url}")
            else :
                landing_page = Page(
                site_id=page.site_id,
                page_url=landing_url,
                page_title=None,
                status="new",
                is_auth_detected=True,
                created_on=datetime.utcnow(),
                created_by=requested_by
            )
                db.add(landing_page)
                db.commit()
                db.refresh(landing_page)
                logger.info(f"[AUTH] Created landing page record | id={landing_page.id}")

            pages_to_process = [landing_page]
            logger.info("[AUTH] Discovering authenticated URLs")

            # ---------------------------------------------
            # Discover authenticated URLs
            # ---------------------------------------------

            extractor = URLExtractor(driver, logger)

            auth_urls = extractor.extract_urls(landing_url)
            
            base_domain = urlparse(landing_url).netloc

            for url in auth_urls:
                if url == landing_url:
                    continue

                parsed = urlparse(url)
                if parsed.netloc != base_domain:
                    continue

                if "logout" in url.lower() or "signout" in url.lower():
                    continue

                existing = db.query(Page).filter(Page.page_url == url).first()

                if existing:
                    pages_to_process.append(existing)
                    continue

                new_page = Page(
                   site_id=page.site_id,
                   page_url=url,
                   status=PageStatus.NEW,
                   is_auth_detected=True,
                   created_on=datetime.utcnow(),
                   created_by=requested_by
                )

                db.add(new_page)
                db.commit()
                db.refresh(new_page)

                pages_to_process.append(new_page)

            logger.info(f"[AUTH] Total authenticated pages discovered: {len(pages_to_process)}")

            # ---------------------------------------------
            # Parallel processing of pages
            # ---------------------------------------------
            loop = asyncio.get_running_loop()

            tasks = []

            for p in pages_to_process:
                tasks.append(
                    loop.run_in_executor(
                        None,
                        self._run_page_pipeline,
                        driver,
                        p,
                        requested_by,
                        loop,
                    )
                )
            
            await asyncio.gather(*tasks)
            
        finally:
            driver.quit()
            db.close()
                

    # =========================================================================
    # STEP 1 — PAGE EXTRACT  (full site crawl, pipeline entry point)
    # =========================================================================

    async def process_page_extract(self, body: dict):
        logger.info(f"[PAGE_EXTRACT] Started | payload={body}")

        site_id      = body["site_id"]
        site_url     = body["site_url"]
        requested_by = body["requested_by"]

        db = SessionLocal()
        try:
            site = db.query(Site).filter(Site.id == site_id).first()
            if not site or site.status == "Paused":
                logger.info(f"[PAGE_EXTRACT] Skipped — site paused or not found | site_id={site_id}")
                return

            site.status     = "Processing"
            site.updated_on = datetime.utcnow()
            site.updated_by = requested_by
            db.commit()
            await self._notify_site_ws(site.id, requested_by=requested_by)


            loop   = asyncio.get_running_loop()
            driver = get_driver()

            try:
                urls = await loop.run_in_executor(
                    None, URLExtractor(driver, logger).extract_urls, site_url
                )

                base_domain = urlparse(site_url).netloc

                for url in urls:
                    if not db.query(Page).filter(Page.page_url == url).first():
                        db.add(Page(
                            site_id=site.id,
                            page_url=url,
                            status=PageStatus.NEW,
                            is_auth_detected=False,
                            created_on=datetime.utcnow(),
                            created_by=requested_by,
                        ))

                    parsed = urlparse(url)
                    if parsed.netloc != base_domain:
                        if not db.query(SiteAlias).filter(
                            SiteAlias.site_id == site.id,
                            SiteAlias.site_alias_url == parsed.netloc,
                        ).first():
                            db.add(SiteAlias(site_id=site.id, site_alias_url=parsed.netloc))

                db.commit()

            finally:
                driver.quit()

            logger.info(f"[PAGE_EXTRACT] Completed | site_id={site.id}")

            pages = db.query(Page).filter(
                Page.site_id == site.id,
                Page.status  == PageStatus.NEW,
            ).all()

            for page in pages:
                await rabbitmq_producer.publish_message(
                    settings.PAGE_ANALYSE_QUEUE,
                    {
                        "event":        "PAGE_ANALYSE",
                        "page_id":      page.id,
                        "requested_by": requested_by,
                        "timestamp":    datetime.utcnow().isoformat(),
                    },
                    priority=5,
                )

        finally:
            db.close()

    # =========================================================================
    # STEP 2 — PAGE ANALYSE
    # =========================================================================

    async def process_page_analyse(self, body: dict):
        logger.info(f"[PAGE_ANALYSE] Started | payload={body}")

        page_id      = body["page_id"]
        requested_by = body["requested_by"]

        db   = SessionLocal()
        page = db.query(Page).filter(Page.id == page_id).first()

        # Anti-loop guard: only process pages that are truly new
        if not page or page.status != PageStatus.NEW:
            db.close()
            return

        # ── Pause check ──────────────────────────────────────────────────────
        if self._is_paused(page.site_id):
            logger.info(f"[PAGE_ANALYSE] Site paused — holding page_id={page_id}")
            db.close()
            return

        self._set_page_status(db, page, PageStatus.GENERATING_METADATA, requested_by)
        db.commit()
        await self._notify_ws(page, requested_by)

        driver         = get_driver()
        llm            = LLMWrapper(db=db)
        prompt_manager = PromptManager()
        loop           = asyncio.get_running_loop()

        try:
            await loop.run_in_executor(
                None,
                PageAnalysisService(
                    driver=driver, logger=logger, llm=llm, prompt_manager=prompt_manager
                ).analyze_page,
                page.id,
                page.page_url,
                requested_by,
            )

            # ── Pause check after heavy work ─────────────────────────────────
            if self._is_paused(page.site_id):
                logger.info(f"[PAGE_ANALYSE] Site paused after analysis — page_id={page_id}")
                db.close()
                return

            await rabbitmq_producer.publish_message(
                settings.TEST_SCENARIO_QUEUE,
                {
                    "event":        "TEST_SCENARIO_QUEUE",
                    "page_id":      page.id,
                    "requested_by": requested_by,
                    "timestamp":    datetime.utcnow().isoformat(),
                },
                priority=5,
            )

        except Exception:
            # Roll back to "new" so resume can retry
            self._set_page_status(db, page, PageStatus.NEW, requested_by)
            db.commit()
            raise

        finally:
            driver.quit()
            db.close()

    # =========================================================================
    # STEP 3 — TEST SCENARIO GENERATE
    # =========================================================================

    async def process_test_scenario(self, body: dict):
        logger.info(f"[TEST_SCENARIO] Started | payload={body}")

        page_id      = body["page_id"]
        requested_by = body["requested_by"]

        db = SessionLocal()
        try:
            page = db.query(Page).filter(Page.id == page_id).first()
            if not page:
                return

            # ── Pause check ──────────────────────────────────────────────────
            if self._is_paused(page.site_id):
                logger.info(f"[TEST_SCENARIO] Site paused — holding page_id={page_id}")
                return

            self._set_page_status(db, page, PageStatus.GENERATING_TEST_SCENARIOS, requested_by)
            db.commit()
            await self._notify_ws(page, requested_by)

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                TestScenarioService(
                    llm=LLMWrapper(db=db), prompt_manager=PromptManager(), logger=logger
                ).generate,
                page_id,
                requested_by,
            )

            # ── Pause check after heavy work ─────────────────────────────────
            if self._is_paused(page.site_id):
                logger.info(f"[TEST_SCENARIO] Site paused after generation — page_id={page_id}")
                # Page status stays "generating_test_scenarios" so resume
                # knows to re-emit TEST_SCENARIO_GENERATE
                return

            # Detect auth requirements and tag scenarios + page
            auth_required = self._detect_auth_requirements(db, page_id)
            if auth_required:
                page = db.query(Page).filter(Page.id == page_id).first()
                if page:
                    page.is_auth_detected = True
                    page.updated_on       = datetime.utcnow()
                    page.updated_by       = requested_by
                    db.commit()
                    logger.info(f"[TEST_SCENARIO] Page {page_id} → is_auth_detected=True")

            await rabbitmq_producer.publish_message(
                settings.TEST_CASE_QUEUE,
                {
                    "event":        "TEST_CASE_QUEUE",
                    "page_id":      page_id,
                    "requested_by": requested_by,
                    "timestamp":    datetime.utcnow().isoformat(),
                },
                priority=5,
            )

            logger.info(f"[TEST_SCENARIO] Completed | page_id={page_id}")

        except Exception:
            logger.exception("[TEST_SCENARIO] Failed")
            raise

        finally:
            db.close()

    # =========================================================================
    # STEP 4 — TEST CASE GENERATE
    # =========================================================================

    async def process_test_case(self, body: dict):
        logger.info(f"[TEST_CASE] Started | payload={body}")

        page_id      = body["page_id"]
        requested_by = body["requested_by"]
        # Optional: scenario_id present only on targeted re-run
        scenario_id  = body.get("scenario_id")

        db = SessionLocal()
        try:
            page = db.query(Page).filter(Page.id == page_id).first()
            if not page:
                return

            # ── Pause check ──────────────────────────────────────────────────
            if self._is_paused(page.site_id):
                logger.info(f"[TEST_CASE] Site paused — holding page_id={page_id}")
                return

            self._set_page_status(db, page, PageStatus.GENERATING_TEST_CASES, requested_by)
            db.commit()
            await self._notify_ws(page, requested_by, scenario_id)

            loop = asyncio.get_running_loop()

            if scenario_id:
                # ── Targeted re-run: single scenario only ─────────────────
                logger.info(f"[TEST_CASE] Targeted re-run | scenario_id={scenario_id}")
                await loop.run_in_executor(
                    None,
                    TestCaseService(
                        llm=LLMWrapper(db=db), prompt_manager=PromptManager(), logger=logger
                    ).generate_for_scenario,
                    page_id,
                    scenario_id,
                    requested_by,
                )
            else:
                # ── Normal full-page generation ───────────────────────────
                await loop.run_in_executor(
                    None,
                    TestCaseService(
                        llm=LLMWrapper(db=db), prompt_manager=PromptManager(), logger=logger
                    ).generate,
                    page_id,
                    requested_by,
                )

            # ── Pause check after heavy work ─────────────────────────────────
            if self._is_paused(page.site_id):
                logger.info(f"[TEST_CASE] Site paused after generation — page_id={page_id}")
                return

            # Auth check + login + post-auth page discovery
            login_test_case = self._get_login_test_case(db, page_id)
            if login_test_case:
                logger.info(f"[AUTH] Login test case detected | page_id={page_id}")

                body = {
                    "test_case_id": login_test_case.id,
                    "requested_by": requested_by
                }
                await self._perform_login_and_discover(body)

            await rabbitmq_producer.publish_message(
                settings.TEST_SCRIPT_QUEUE,
                {
                    "event":        "TEST_SCRIPT_QUEUE",
                    "page_id":      page_id,
                    "scenario_id":  scenario_id,   # None on full run, int on re-run
                    "requested_by": requested_by,
                    "timestamp":    datetime.utcnow().isoformat(),
                },
                priority=5,
            )

            logger.info(f"[TEST_CASE] Completed | page_id={page_id}")

        except Exception:
            logger.exception("[TEST_CASE] Failed")
            raise

        finally:
            db.close()

    # =========================================================================
    # STEP 5 — TEST SCRIPT GENERATE
    # =========================================================================

    async def process_test_script(self, body: dict):
        logger.info(f"[TEST_SCRIPT] Started | payload={body}")

        page_id      = body["page_id"]
        requested_by = body["requested_by"]
        scenario_id  = body.get("scenario_id")   # None = all scenarios, int = targeted

        db = SessionLocal()
        try:
            page = db.query(Page).filter(Page.id == page_id).first()
            if not page:
                logger.warning(f"[TEST_SCRIPT] Page {page_id} not found — skipping")
                return

            # ── Pause check ──────────────────────────────────────────────────
            if self._is_paused(page.site_id):
                logger.info(f"[TEST_SCRIPT] Site paused — holding page_id={page_id}")
                return

            self._set_page_status(db, page, PageStatus.GENERATING_TEST_SCRIPTS, requested_by)
            db.commit()
            await self._notify_ws(page, requested_by, scenario_id)

            # Guard — need at least one scenario
            scenario_q = db.query(TestScenario).filter(TestScenario.page_id == page_id)
            if scenario_id:
                scenario_q = scenario_q.filter(TestScenario.id == scenario_id)

            if scenario_q.count() == 0:
                logger.warning(f"[TEST_SCRIPT] No scenarios found | page_id={page_id} — skipping")
                await self._finalize_page(db, page, requested_by)
                return

            # Resolve login credentials if auth was detected
            require_login = page.is_auth_detected
            username      = None
            password      = None

            if require_login:
                auth_tc = self._get_login_test_case(db, page_id)
                if auth_tc:
                    resolved = TestCredentialService(llm=LLMWrapper(db=db), logger=logger).resolve(
                        page_id, auth_tc.data.get("test_data", {})
                    )
                    for key, value in resolved.items():
                        if "email" in key.lower() or "username" in key.lower():
                            username = value
                        if "password" in key.lower():
                            password = value

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                TestScriptService(
                    llm=LLMWrapper(db=db), prompt_manager=PromptManager(), logger=logger
                ).generate_scripts_for_page,
                page,
                require_login,
                username,
                password,
                requested_by,
                scenario_id,   # None = all, int = targeted
            )

            # ── Pause check after heavy work ─────────────────────────────────
            if self._is_paused(page.site_id):
                logger.info(f"[TEST_SCRIPT] Site paused after generation — page_id={page_id}")
                return

            await self._finalize_page(db, page, requested_by, scenario_id)

            logger.info(f"[TEST_SCRIPT] Completed | page_id={page_id}")

        except Exception:
            logger.exception("[TEST_SCRIPT] Failed")
            raise

        finally:
            db.close()

    async def _finalize_page(self, db, page: Page, requested_by: int , scenario_id: int | None = None):
        """Mark page as done, notify WS, emit TEST_EXECUTION."""
        self._set_page_status(db, page, PageStatus.DONE, requested_by)
        db.commit()
        await self._notify_ws(page, requested_by, scenario_id)

        if page.site_id:
            remaining_pages = db.query(Page).filter(
            Page.site_id == page.site_id,
            Page.status != PageStatus.DONE
            ).count()

            if remaining_pages == 0:
                site = db.query(Site).filter(Site.id == page.site_id).first()
                if site:
                    site.status = "Done"
                    site.updated_on = datetime.utcnow()
                    site.updated_by = requested_by
                    db.commit()
                    await self._notify_site_ws(page.site_id, requested_by=requested_by)
                    logger.info(
                        f"[SITE_COMPLETE] Site processing completed | site_id={site.id}"
                    )

        payload = {
            "event": "TEST_EXECUTION_QUEUE",
            "page_id": page.id,
            "requested_by": requested_by,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if scenario_id is not None:
            payload["scenario_id"] = scenario_id
        try:
            await rabbitmq_producer.publish_message(
            settings.TEST_EXECUTION_QUEUE,
            payload,
            priority=5,
            )
        except Exception as e:
            logger.error(
                f"[TEST_EXECUTION_QUEUE] Failed to publish | page_id={page.id} | error={e}"
            )

    # =========================================================================
    # STEP 6 — TEST EXECUTION 
    # =========================================================================

    async def process_test_execution(self, body: dict):
        """
        Execute the generated Selenium scripts for every test case on the page
        and persist results to the test_execution table.

        One TestExecution row is written per TestCase per execution run.
        Re-runs update existing rows (upsert) so history doesn't accumulate.

        Body keys:
        page_id      — page to execute
        requested_by — user id → stored as executed_by
        scenario_id  — (optional) targeted single-scenario execution
        test_suite_id — (optional) FK for grouping runs
        """
        logger.info(f"[TEST_EXECUTION] Started | payload={body}")

        page_id       = body["page_id"]
        requested_by  = body["requested_by"]
        scenario_id   = body.get("scenario_id")    # None = all scenarios
        test_suite_id = body.get("test_suite_id")  # optional grouping

        db = SessionLocal()
        try:
            page = db.query(Page).filter(Page.id == page_id).first()
            if not page:
                logger.warning(f"[TEST_EXECUTION] Page {page_id} not found — skipping")
                return

            # Pause check — executions are long-running Selenium runs
            if page.site_id and self._is_paused(page.site_id):
                logger.info(
                    f"[TEST_EXECUTION] Site paused — holding | page_id={page_id}"
                )
                return

            loop = asyncio.get_running_loop()

            await loop.run_in_executor(
                None,
                TestExecutionService(
                    llm=LLMWrapper(db=db),
                    prompt_manager=PromptManager(),
                    logger=logger,
                ).execute_page,
                page,
                requested_by,
                scenario_id,
                test_suite_id,
            )

            logger.info(f"[TEST_EXECUTION] Completed | page_id={page_id}")

            # Notify WebSocket — page execution finished
            # Re-fetch page to get latest state for the WS payload
            db.refresh(page)
            await self._notify_ws(page, requested_by, scenario_id)

        except Exception:
            logger.exception("[TEST_EXECUTION] Failed")
            raise

        finally:
            db.close()

    # =========================================================================
    # STEP 2b — PAGE EXTRACT SINGLE  (post-auth page discovery only)
    # =========================================================================

    async def process_page_extract_single(self, body: dict):
        """
        Extract URLs from a single post-auth landing page.
        Only inserts URLs not already in the Page table.
        Emits PAGE_ANALYSE only for the newly inserted pages.
        """
        logger.info(f"[PAGE_EXTRACT_SINGLE] Started | payload={body}")

        site_id      = body["site_id"] # can be null if the page is orphaned, but we still want to attempt extraction
        extract_url  = body["extract_url"]
        page_id      = body["page_id"]   # originating page (for logging)
        requested_by = body["requested_by"]

        if not extract_url:
            logger.error(f"[PAGE_EXTRACT_SINGLE] No URL in payload — skipping | body={body}")
            return
        
        db = SessionLocal()
        try:

            site = None
            base_domain = None

            if site_id and self._is_paused(site_id):
                logger.info(
                    f"[PAGE_EXTRACT_SINGLE] Site paused — holding | site_id={site_id}"
                )
                return

            # ─────────────────────────────────────────────────────────────────
            # CASE A — Standalone single page where site_id is None
            # The page already exists; just forward it to PAGE_ANALYSE.
            # ─────────────────────────────────────────────────────────────────
            if not site_id:
                page = db.query(Page).filter(Page.id == page_id).first()
                if not page:
                    logger.warning(
                        f"[PAGE_EXTRACT_SINGLE] Standalone page {page_id} not found — skipping"
                    )
                    return

                # Guard: only process if still in initial state
                if page.status != PageStatus.NEW:
                    logger.info(
                        f"[PAGE_EXTRACT_SINGLE] Standalone page {page_id} already "
                        f"processing (status={page.status}) — skipping"
                    )
                    return

                logger.info(
                    f"[PAGE_EXTRACT_SINGLE] Standalone page — forwarding to PAGE_ANALYSE | "
                    f"page_id={page_id} url={extract_url}"
                )
                
                await rabbitmq_producer.publish_message(
                    settings.PAGE_ANALYSE_QUEUE,
                    {
                        "event":        "PAGE_ANALYSE",
                        "page_id":      page_id,
                        "requested_by": requested_by,
                        "timestamp":    datetime.utcnow().isoformat(),
                    },
                    priority=5,
                )
                return


            # ─────────────────────────────────────────────────────────────────
            # CASE B — Normal flow with site_id:
            # Insert new page if URL not seen before, then emit PAGE_ANALYSE.
            # ─────────────────────────────────────────────────────────────────
            site = db.query(Site).filter(Site.id == site_id).first()
            if not site:
                logger.warning(
                    f"[PAGE_EXTRACT_SINGLE] Site {site_id} not found — skipping"
                )
                return

            loop   = asyncio.get_running_loop()
            driver = get_driver()

            try:
                urls = await loop.run_in_executor(
                    None, URLExtractor(driver, logger).extract_urls, extract_url
                )

                base_domain = urlparse(extract_url).netloc
                new_pages   = []

                for url in urls:
                    # Strict deduplication — DB is source of truth
                    if not db.query(Page).filter(Page.page_url == url).first():
                        new_page = Page(
                            site_id=site.id,
                            page_url=url,
                            status=PageStatus.NEW,
                            is_auth_detected=False,
                            created_on=datetime.utcnow(),
                            created_by=requested_by,
                        )
                        db.add(new_page)
                        new_pages.append(new_page)

                    parsed = urlparse(url)
                    if parsed.netloc != base_domain:
                        alias_exists = db.query(SiteAlias).filter(
                            SiteAlias.site_id == site.id,
                            SiteAlias.site_alias_url == parsed.netloc,
                        ).first()

                        if not alias_exists:
                            db.add(
                                SiteAlias(
                                    site_id=site.id,
                                    site_alias_url=parsed.netloc
                                )
                            )

                db.commit()
                for np in new_pages:
                    db.refresh(np)

            finally:
                driver.quit()

            logger.info(
                f"[PAGE_EXTRACT_SINGLE] Done | origin_page_id={page_id} "
                f"new_pages={len(new_pages)}"
            )

            # Emit PAGE_ANALYSE
            for new_page in new_pages:
                await rabbitmq_producer.publish_message(
                    settings.PAGE_ANALYSE_QUEUE,
                    {
                        "event":        "PAGE_ANALYSE",
                        "page_id":      new_page.id,
                        "requested_by": requested_by,
                        "timestamp":    datetime.utcnow().isoformat(),
                    },
                    priority=6,
                )

        finally:
            db.close()

    # =========================================================================
    # PAUSE / RESUME
    # =========================================================================

    async def process_resume(self, body: dict):
        """
        Called when the user clicks Resume.
        API must set site.status = "Processing" BEFORE publishing this event.

        Scans every page for the site that is not yet "done" and re-emits
        the correct queue message based on its current status.
        """
        logger.info(f"[RESUME] Started | payload={body}")

        site_id      = body["site_id"]
        requested_by = body["requested_by"]

        db = SessionLocal()
        try:
            site = db.query(Site).filter(Site.id == site_id).first()
            if not site:
                logger.warning(f"[RESUME] Site {site_id} not found")
                return

            if site.status == "Paused":
                logger.warning(
                    f"[RESUME] Site {site_id} is still Paused — "
                    "API should set status=Processing before publishing RESUME"
                )
                return

            # All pages that are not yet done
            pages = db.query(Page).filter(
                Page.site_id != None,
                Page.site_id == site_id,
                Page.status  != PageStatus.DONE,
            ).all()

            resumed = 0
            for page in pages:
                entry = _RESUME_MAP.get(page.status)
                if not entry:
                    # Unknown or done status — skip
                    continue

                queue, event, priority = entry
                await rabbitmq_producer.publish_message(
                    queue,
                    {
                        "event":        event,
                        "page_id":      page.id,
                        "requested_by": requested_by,
                        "timestamp":    datetime.utcnow().isoformat(),
                    },
                    priority=priority,
                )
                resumed += 1
                logger.info(
                    f"[RESUME] Re-queued | page_id={page.id} "
                    f"status='{page.status}' → event={event}"
                )

            logger.info(f"[RESUME] Completed | site_id={site_id} pages_resumed={resumed}")

        finally:
            db.close()

    # =========================================================================
    # AUTH CREDENTIAL UPDATE  (standalone entry point from frontend)
    # =========================================================================

    async def process_auth_credential_update(self, body: dict):
        """
        Triggered when the user updates login credentials in the frontend.
        Scope: re-run login only + crawl any newly discovered post-auth pages.

        Flow:
          1. Resolve new credentials from TestCredentialService.
          2. Find the site's login page (is_auth_detected=True).
          3. Drive Selenium to log in with the new credentials.
          4. Emit PAGE_EXTRACT_SINGLE for the landing URL if it's new.
             New pages flow independently through the full pipeline.
        """
        logger.info(f"[AUTH_UPDATE] Started | payload={body}")

        site_id      = body["site_id"]
        requested_by = body["requested_by"]
        # Caller may pass pre-resolved credentials directly
        new_username = body.get("username")
        new_password = body.get("password")

        db = SessionLocal()
        try:
            # ── Pause check ──────────────────────────────────────────────────
            if self._is_paused(site_id):
                logger.info(f"[AUTH_UPDATE] Site paused — skipping | site_id={site_id}")
                return

            # Find a page for this site that has auth detected
            auth_page = db.query(Page).filter(
                Page.site_id         == site_id,
                Page.is_auth_detected == True,
            ).first()

            if not auth_page:
                logger.warning(
                    f"[AUTH_UPDATE] No auth-detected page found for site {site_id}"
                )
                return

            # Resolve credentials — prefer directly passed values,
            # fall back to credential service lookup
            if not new_username or not new_password:
                auth_tc = self._get_login_test_case(db, auth_page.id)
                if not auth_tc:
                    logger.warning(
                        f"[AUTH_UPDATE] No login test case for page {auth_page.id}"
                    )
                    return

                resolved = TestCredentialService(
                    llm=LLMWrapper(db=db), logger=logger
                ).resolve(auth_page.id, auth_tc.data.get("test_data", {}))

                for key, value in resolved.items():
                    if "email" in key.lower() or "username" in key.lower():
                        new_username = value
                    if "password" in key.lower():
                        new_password = value

            if not new_username or not new_password:
                logger.warning("[AUTH_UPDATE] Could not resolve credentials — aborting")
                return

            # Drive Selenium login with new credentials
            driver         = get_driver()
            llm            = LLMWrapper(db=db)
            prompt_manager = PromptManager()

            try:
                driver.get(auth_page.page_url)

                analyzer = PageAnalysisService(
                    driver=driver, logger=logger, llm=llm, prompt_manager=prompt_manager
                )
                success = analyzer.login_to_website(
                    username=new_username, password=new_password
                )

                if not success:
                    logger.warning("[AUTH_UPDATE] Login failed with new credentials")
                    return

                logger.info("[AUTH_UPDATE] Login successful with new credentials")
                landing_url = driver.current_url

                # Only extract if the landing URL is new
                if db.query(Page).filter(Page.page_url == landing_url).first():
                    logger.info(
                        f"[AUTH_UPDATE] Landing page already known: {landing_url} — done"
                    )
                    return

                logger.info(f"[AUTH_UPDATE] New landing page: {landing_url} — triggering extract")
                await rabbitmq_producer.publish_message(
                    settings.PAGE_EXTRACT_SINGLE_QUEUE,
                    {
                        "event":        "PAGE_EXTRACT_SINGLE_QUEUE",
                        "site_id":      site_id,
                        "extract_url":     landing_url,
                        "page_id":      auth_page.id,
                        "requested_by": requested_by,
                        "timestamp":    datetime.utcnow().isoformat(),
                    },
                    priority=6,
                )

            finally:
                driver.quit()

            logger.info(f"[AUTH_UPDATE] Completed | site_id={site_id}")

        finally:
            db.close()

    # =========================================================================
    # SCENARIO RE-RUN  (targeted single-scenario re-run from frontend)
    # =========================================================================

    async def process_scenario_rerun(self, body: dict):
        """
        Triggered when the user clicks "Run Again" on a specific scenario
        in the frontend.

        Sets page.status = "generating_test_cases" and emits
        TEST_CASE_QUEUE with scenario_id so only that scenario's
        test cases and script are regenerated.
        """
        logger.info(f"[SCENARIO_RERUN] Started | payload={body}")

        scenario_id  = body["scenario_id"]
        requested_by = body["requested_by"]

        db = SessionLocal()
        try:
            scenario = db.query(TestScenario).filter(
                TestScenario.id == scenario_id
            ).first()

            if not scenario:
                logger.warning(f"[SCENARIO_RERUN] Scenario {scenario_id} not found")
                return

            page = db.query(Page).filter(Page.id == scenario.page_id).first()
            if not page:
                logger.warning(f"[SCENARIO_RERUN] Page {scenario.page_id} not found")
                return

            # ── Pause check ──────────────────────────────────────────────────
            if self._is_paused(page.site_id):
                logger.info(
                    f"[SCENARIO_RERUN] Site paused — skipping | site_id={page.site_id}"
                )
                return

            # Reset page status so the pipeline re-enters correctly
            self._set_page_status(db, page, PageStatus.GENERATING_TEST_CASES, requested_by)
            db.commit()
            await self._notify_ws(page, requested_by)

            # Emit targeted TEST_CASE_QUEUE (scenario_id carried through)
            await rabbitmq_producer.publish_message(
                settings.TEST_CASE_QUEUE,
                {
                    "event":        "TEST_CASE_QUEUE",
                    "page_id":      page.id,
                    "scenario_id":  scenario_id,
                    "requested_by": requested_by,
                    "timestamp":    datetime.utcnow().isoformat(),
                },
                priority=7,   # Higher priority — user-initiated
            )

            logger.info(
                f"[SCENARIO_RERUN] Queued | "
                f"scenario_id={scenario_id} page_id={page.id}"
            )

        finally:
            db.close()
    
    def _run_page_pipeline(self, driver, page: Page, requested_by: int, loop):
        """
        Synchronous pipeline executed inside a thread-pool (run_in_executor).
        ``loop`` is the main event loop and is required to schedule coroutines
        safely from this thread via asyncio.run_coroutine_threadsafe().
        """
        def _notify(pg):
            future = asyncio.run_coroutine_threadsafe(
                self._notify_ws(pg, requested_by), loop
            )
            try:
                future.result(timeout=10)
            except Exception as exc:
                logger.warning(f"[PIPELINE] WS notify failed | page_id={pg.id} | {exc}")

        logger.info(f"[PIPELINE] Running pipeline | page_id={page.id}")
        db = SessionLocal()
        llm = LLMWrapper(db=db)
        prompt_manager = PromptManager()

        analyzer = PageAnalysisService(
            driver=driver,
            logger=logger,
            llm=llm,
            prompt_manager=prompt_manager
        )

        try:
            # STEP 1 — ANALYZE PAGE
            page.status = PageStatus.GENERATING_METADATA
            db.commit()
            _notify(page)

            analyzer.analyze_page(
                page_id=page.id,
                page_url=page.page_url,
                requested_by=requested_by
            )

            # STEP 2 — GENERATE SCENARIOS
            page.status = PageStatus.GENERATING_TEST_SCENARIOS
            db.commit()
            _notify(page)

            TestScenarioService(
                llm=llm,
                prompt_manager=prompt_manager,
                logger=logger
            ).generate(page.id, requested_by)

            # STEP 3 — GENERATE TEST CASES
            page.status = PageStatus.GENERATING_TEST_CASES
            db.commit()
            _notify(page)

            TestCaseService(
                llm=llm,
                prompt_manager=prompt_manager,
                logger=logger
            ).generate(page.id, requested_by)

            # STEP 4 — GENERATE TEST SCRIPTS
            page.status = PageStatus.GENERATING_TEST_SCRIPTS
            db.commit()
            _notify(page)

            TestScriptService(
                llm=llm,
                prompt_manager=prompt_manager,
                logger=logger
            ).generate_scripts_for_page(
               page,
               require_login=True,
               username=None,
               password=None,
               requested_by=requested_by
            )
            logger.info(f"[PIPELINE] Executing tests | page_id={page.id}")
            TestExecutionService(
                llm=LLMWrapper(db=db),
                prompt_manager=PromptManager(),
                logger=logger,
            ).execute_page(
                page,
                requested_by,
                None,
                None
            )

            page.status = PageStatus.DONE
            db.commit()
            _notify(page)

        finally:
            db.close()
        logger.info(f"[PIPELINE] Completed pipeline | page_id={page.id}")

    async def _notify_site_ws(self, site_id: int, requested_by: int = None):
        """
        Publish SITE_STATUS_UPDATE event for WebSocket broadcasting.
        """
        db = SessionLocal()
        try :
            # total pages
            page_count = db.query(Page).filter(
                Page.site_id == site_id
            ).count()

            # total scenarios
            scenario_count = (
                db.query(TestScenario)
                .join(Page, Page.id == TestScenario.page_id)
                .filter(Page.site_id == site_id)
                .count()
            )

            # total test cases
            test_case_count = (
                db.query(TestCase)
                .join(Page, Page.id == TestCase.page_id)
                .filter(Page.site_id == site_id)
                .count()
            )
            site = db.query(Site).filter(Site.id == site_id).first()
            payload = {
                "site_id": site_id,
                "site_status": site.status if site else None,
                "requested_by": requested_by,
                "page_count": page_count,
                "test_scenario_count": scenario_count,
                "test_case_count": test_case_count,
            }
            message = {
                "event": "SITE_STATUS_UPDATE",
                "payload": payload,
            }
            await rabbitmq_producer.publish_message(
                settings.SITE_STATUS_UPDATE_QUEUE,
                message
            )
            logger.info(
                f"[SITE_WS_NOTIFY] site_id={site_id} "
                f"pages={page_count} scenarios={scenario_count} cases={test_case_count}"
            )
        except Exception as e:
            logger.error(
                f"[SITE_WS_NOTIFY] Failed | site_id={site_id} error={e}"
            )  

        finally:
            db.close()


worker_service = WorkerService()