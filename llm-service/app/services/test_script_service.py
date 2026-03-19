import json
import os
import re
from datetime import datetime
from pathlib import Path
from app.config.database import SessionLocal
from shared_orm.models.test_scenario import TestScenario
from shared_orm.models.test_case import TestCase


class TestScriptService:
    """
    Generates and persists Selenium/Java test scripts directly onto the
    TestScenario record (scenario.script + scenario.script_path columns).

    Supports two modes:
      - Full page:      generate_scripts_for_page(..., scenario_id=None)
                        → generates for ALL scenarios on the page
      - Targeted rerun: generate_scripts_for_page(..., scenario_id=<int>)
                        → generates only for that one scenario
    """

    def __init__(
        self,
        llm,
        prompt_manager,
        logger,
        testing_tool: str = "selenium",
        language: str = "python",
        selenium_version: str = "4",
        wait_time: str = None,
        auth_data: dict = None,
    ):
        self.llm              = llm
        self.prompt_manager   = prompt_manager
        self.logger           = logger
        self.testing_tool     = testing_tool
        self.language         = language
        self.selenium_version = selenium_version
        self.wait_time        = wait_time
        self.auth_data        = auth_data or {}

    # -----------------------------------------------------------------------
    # ENTRY POINT — called via run_in_executor from WorkerService
    # -----------------------------------------------------------------------

    def generate_scripts_for_page(
        self,
        page,
        require_login: bool,
        username: str,
        password: str,
        requested_by: int,
        scenario_id: int = None,      # None = all scenarios, int = targeted rerun
    ):
        """
        Generate and persist scripts for scenarios on a page.

        Args:
            page:          ORM Page object (page_source, page_metadata populated).
            require_login: True if this page requires authentication.
            username:      Resolved login credential (or None).
            password:      Resolved login password (or None).
            requested_by:  User ID for audit columns.
            scenario_id:   If set, only generate for this specific scenario.
        """
        minimized_html = page.page_source   or ""
        page_metadata  = page.page_metadata or {}

        with SessionLocal() as db:
            query = db.query(TestScenario).filter(TestScenario.page_id == page.id)

            if scenario_id is not None:
                query = query.filter(TestScenario.id == scenario_id)
                self.logger.info(
                    f"[TEST_SCRIPT] Targeted rerun | "
                    f"page_id={page.id} scenario_id={scenario_id}"
                )

            scenarios = query.all()

            if not scenarios:
                self.logger.warning(
                    f"[TEST_SCRIPT] No scenarios found | "
                    f"page_id={page.id} scenario_id={scenario_id} — skipping"
                )
                return

            for scenario in scenarios:
                try:
                    self.logger.info(
                        f"[TEST_SCRIPT] Generating | "
                        f"scenario_id={scenario.id} title='{scenario.title}'"
                    )

                    scenario_dict = {
                        "name":          scenario.title,
                        "data":          scenario.data     or {},
                        "category":      scenario.category or "",
                        "requires_auth": scenario.requires_auth,
                    }

                    # Gather all TestCase rows for this scenario and pass them
                    tc_rows = db.query(TestCase).filter(
                        TestCase.test_scenario_id == scenario.id
                    ).all()

                    test_cases_list = []
                    for tc in tc_rows:
                        test_cases_list.append({
                            "name": tc.title,
                            "data": tc.data or {},
                            "is_valid": tc.is_valid,
                            "is_valid_default": tc.is_valid_default,
                            "expected_outcome": tc.expected_outcome,
                            "validation": tc.validation,
                        })

                    code, filename, script_path = self.generate_script_for_test_case(
                        scenario=scenario_dict,
                        test_cases=test_cases_list,
                        page_metadata=page_metadata,
                        minimized_html=minimized_html,
                        require_login=require_login,
                        username=username,
                        password=password,
                    )

                    if not code:
                        self.logger.warning(
                            f"[TEST_SCRIPT] Empty script | "
                            f"scenario_id={scenario.id} — skipping"
                        )
                        continue

                    # Persist directly onto the scenario record
                    scenario.script      = code
                    scenario.script_path = script_path
                    scenario.updated_on  = datetime.utcnow()
                    scenario.updated_by  = requested_by

                    self.logger.debug(
                        f"[TEST_SCRIPT] Saved | "
                        f"scenario_id={scenario.id} path={script_path}"
                    )

                except Exception as e:
                    # One failure must not block the remaining scenarios
                    self.logger.error(
                        f"[TEST_SCRIPT] Failed | scenario_id={scenario.id} error={e}"
                    )
                    continue

            db.commit()
            self.logger.info(
                f"[TEST_SCRIPT] All scripts committed | page_id={page.id}"
            )

    # -----------------------------------------------------------------------
    # CORE GENERATION
    # -----------------------------------------------------------------------

    def generate_script_for_test_case(
        self,
        scenario: dict,
        test_cases: list,
        page_metadata: dict,
        minimized_html: str,
        require_login: bool,
        username: str,
        password: str,
    ):
        """
        Generate a Selenium/Java test script for a single scenario via LLM.

        Returns:
            tuple: (code: str, filename: str, script_path: str)
                   Returns ("", None, None) on any failure.
        """
        captcha_wait_time = self.wait_time or "2 minutes (120 seconds)"

        try:
            system_prompt = self.prompt_manager.get_prompt(
                "generate_script", "system", tool=self.testing_tool
            ).format(
                selenium_version=self.selenium_version,
                language=self.language,
            )

            login_instructions = "yes" if (require_login and username and password) else "no"

            user_prompt = self.prompt_manager.get_prompt(
                "generate_script", "user", tool=self.testing_tool
            ).format(
                language=self.language,
                selenium_version=self.selenium_version,
                scenario=json.dumps(scenario, indent=2),
                test_cases=json.dumps(test_cases, indent=2),
                page_metadata=json.dumps(page_metadata, indent=2),
                page_source=minimized_html,
                captcha_wait_time=captcha_wait_time,
                login_instructions=login_instructions,
                username=username or "",
                password=password or "",
                auth_data=self.auth_data,
                security_indicators=page_metadata.get("security_indicators", []),
            )

            script_content = self.llm.generate(
                system_prompt, user_prompt, model_type="selenium"
            )

            # Extract code block from LLM markdown response
            if "```python" in script_content:
                code = script_content.split("```python")[1].split("```")[0].strip()
            elif "```java" in script_content:
                code = script_content.split("```java")[1].split("```")[0].strip()
            elif "```" in script_content:
                code = script_content.split("```")[1].strip()
            else:
                code = script_content.strip()

            if not code:
                return "", None, None

            # Write script to disk
            BASE_DIR = Path(__file__).resolve().parents[2]
            SCRIPT_DIR = BASE_DIR / "test_scripts"
            SCRIPT_DIR.mkdir(parents=True, exist_ok=True)

            timestamp      = datetime.now().strftime("%Y%m%d_%H%M%S")

            sanitized_name = re.sub(r"[^a-zA-Z0-9\-_]", "_", scenario["name"])
            sanitized_name = re.sub(r"_+", "_", sanitized_name).strip("_")

            ext = ".py" if "```python" in script_content else ".java"

            filename  = f"test_{timestamp}_{sanitized_name}{ext}"

            script_path = SCRIPT_DIR / filename

            with open(script_path, "w") as f:
                f.write(code)

            self.logger.debug(f"[TEST_SCRIPT] Written to disk | path={script_path}")
            return code, filename, script_path

        except Exception as e:
            self.logger.error(
                f"[TEST_SCRIPT] generate_script_for_test_case failed: {e}"
            )
            return "", None, None