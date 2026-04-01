"""Service layer for test suite execution.

Contains all business logic orchestrated by the worker consumer:

  Responsibilities
  ----------------
  1. Auth validation
       - Ensures auth suites have a login scenario as the first step.
       - Raises ValueError with a user-facing message on misconfiguration.

  2. Login execution  (auth suites only)
       - Runs a targeted login script (TARGETED_LOGIN_SCRIPT) driven by
         __TEST_CASE__ so the browser authenticates with real credentials.
       - Captures Selenium session cookies via COOKIE_CAPTURE_FOOTER.
       - Resolves {VALID_EMAIL}/{VALID_PASSWORD} placeholders from the DB.

  3. Step execution
       - Iterates steps in step_order.
       - Builds the __TEST_CASE__ injection header for every test case.
       - When auth cookies are present, the header restores the session,
         pre-navigates to the target page, and monkey-patches get_driver()
         so the generated script reuses the authenticated driver.
       - Runs the generated scenario.script in a subprocess.

  4. Result tracking
       - Upserts one TestExecution row per test case per step.
       - Accumulates timestamped log entries in TestSuiteExecution.logs.

  5. Status finalisation
       - Sets TestSuiteExecution.status and TestSuite.status on completion.

Status values
-------------
  passed           : every runnable test case passed
  partially_passed : at least one passed and at least one failed
  failed           : all runnable test cases failed (or zero runnable)
  error            : validation error or unexpected exception

TestSuite.status mapping
------------------------
  passed           → "done"
  partially_passed → "failed"
  failed / error   → "failed"

"""

import json
import os
import subprocess
import sys
import re
import tempfile
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.config.logger import logger
from shared_orm.models.page import Page
from shared_orm.models.test_case import TestCase
from shared_orm.models.test_case_credential import TestCaseCredential
from shared_orm.models.test_execution import TestExecution
from shared_orm.models.test_scenario import TestScenario
from shared_orm.models.test_suite import TestSuite
from shared_orm.models.test_suite_execution import TestSuiteExecution
from shared_orm.models.test_suite_step import TestSuiteStep
from app.constants.constants import COOKIE_CAPTURE_FOOTER, TARGETED_LOGIN_SCRIPT,_PLACEHOLDER_RE


# ===========================================================================
# Internal helpers
# ===========================================================================

def _ts() -> str:
    """Return a UTC timestamp string for log entries."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _is_login_scenario(scenario: Optional[TestScenario]) -> bool:
    """
    Single source of truth for login-scenario detection.

    Returns True when:
      - scenario.category is 'auth-positive' or 'auth-negative', OR
      - the word 'login' appears anywhere in the scenario title.

    Returns False when scenario is None.
    """
    if scenario is None:
        return False
    category_match = (scenario.category or "") in ("auth-positive", "auth-negative")
    title_match = "login" in (scenario.title or "").lower()
    return category_match or title_match


def _parse_tc_ids(step: TestSuiteStep) -> List[int]:
    """Parse the comma-separated test_case_ids string into a list of ints."""
    if not step.test_case_ids:
        return []
    try:
        return [int(x.strip()) for x in step.test_case_ids.split(",") if x.strip()]
    except ValueError:
        logger.warning(
            f"[SUITE_EXEC] Malformed test_case_ids on step {step.id}: "
            f"{step.test_case_ids!r}"
        )
        return []


# ===========================================================================
# Script header builder
# ===========================================================================

def build_script_header(tc_payload: dict, auth_cookies: Optional[List[dict]] = None) -> str:
    """
    Build the Python source block prepended to every generated scenario script.

    Without auth_cookies
    --------------------
    Injects __TEST_CASE__ and initialises a fresh Selenium driver.

    With auth_cookies
    -----------------
    Injects __TEST_CASE__, then:
      1. Creates a fresh driver.
      2. Navigates to the site origin so the domain accepts cookies.
      3. Injects every session cookie.
      4. Refreshes so the server sees the restored session.
      5. Monkey-patches sys.modules so the script's get_driver() call
         returns this already-authenticated driver.
      6. Navigates directly to the target page URL.
      7. Sets __COOKIES_AUTH_DONE__ = True so any leftover login/navigation
         blocks in the generated script skip themselves gracefully.
    """
    # Normalise navigation step prefixes so scripts that split on
    # "navigate to " work regardless of the original capitalisation.
    normalised = dict(tc_payload)
    normalised["steps"] = [
        re.sub(
            r"^(Navigate|Go|Open|Visit|Launch)\s+to\s+",
            "navigate to ",
            s,
            flags=re.IGNORECASE,
        ) if isinstance(s, str) else s
        for s in tc_payload.get("steps", [])
    ]

    lines = [
        "import json",
        "import time",
        f"__TEST_CASE__ = {repr(normalised)}",
        "",
    ]

    if auth_cookies:
        first_domain = next(
            (c.get("domain", "").lstrip(".") for c in auth_cookies if c.get("domain")),
            "",
        )
        origin_url = (
            f"https://{first_domain}" if first_domain
            else tc_payload.get("page_origin", "")
        )

        lines += [
            "# ── Auth session restoration ──────────────────────────────────────────",
            "import sys, types",
            "from selenium.webdriver.support.ui import WebDriverWait as _WDW",
            "from app.services.selenium_driver import get_driver as _gd_real",
            "",
            "_auth_driver = _gd_real()",
            f"_origin  = {repr(origin_url)}",
            f"_cookies = {repr(auth_cookies)}",
            "",
            "# Step 1: visit site origin so browser accepts cookies for this domain",
            "if _origin:",
            "    try:",
            "        _auth_driver.get(_origin)",
            "        _WDW(_auth_driver, 10).until(",
            "            lambda d: d.execute_script('return document.readyState') == 'complete'",
            "        )",
            "    except Exception:",
            "        pass",
            "",
            "# Step 2: inject session cookies",
            "for _c in _cookies:",
            "    try:",
            "        _safe = {k: v for k, v in _c.items()",
            "                 if k in ('name','value','path','domain','secure',",
            "                          'httpOnly','expiry','sameSite')}",
            "        _auth_driver.add_cookie(_safe)",
            "    except Exception:",
            "        pass",
            "",
            "# Step 3: refresh so server sees the restored session",
            "try:",
            "    _auth_driver.refresh()",
            "    _WDW(_auth_driver, 10).until(",
            "        lambda d: d.execute_script('return document.readyState') == 'complete'",
            "    )",
            "except Exception:",
            "    pass",
            "",
            "# Step 4: monkey-patch get_driver so the script reuses this driver",
            "_patch_mod = types.ModuleType('app.services.selenium_driver')",
            "_patch_mod.get_driver = lambda: _auth_driver",
            "sys.modules['app.services.selenium_driver'] = _patch_mod",
            "driver = _auth_driver",
            "",
            "# Step 5: navigate directly to the target page",
            f"_target_page_url = {repr(tc_payload.get('page_url', ''))}",
            "if _target_page_url:",
            "    try:",
            "        _auth_driver.get(_target_page_url)",
            "        _WDW(_auth_driver, 10).until(",
            "            lambda d: d.execute_script('return document.readyState') == 'complete'",
            "        )",
            "    except Exception:",
            "        pass",
            "",
            "# Step 6: suppress redundant login/navigation blocks in generated scripts",
            "__COOKIES_AUTH_DONE__ = True",
            "# ── End auth session restoration ──────────────────────────────────────",
            "",
        ]
    else:
        lines += [
            "from app.services.selenium_driver import get_driver as _gd",
            "driver = _gd()",
            "",
        ]

    return "\n".join(lines) + "\n"


# ===========================================================================
# Script runner
# ===========================================================================

def execute_test_script(script: str) -> dict:
    """
    Write *script* to a temp file and run it in a subprocess.

    Sets PYTHONPATH to os.getcwd() (the LLM service root inside the
    container) so that ``from app.services.selenium_driver import get_driver``
    resolves correctly — mirroring test_execution_service.py.

    Returns
    -------
    {
        "success":     bool | None,   # None = timeout or unexpected exception
        "output":      str,           # stdout
        "error":       str,           # stderr
        "return_code": int,
    }
    """
    tmp_file = None
    try:
        if not script.strip():
            return {"success": None, "output": "", "error": "Empty script", "return_code": -1}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(script)
            tmp_file = fh.name

        env = os.environ.copy()
        env["PYTHONPATH"] = os.getcwd()

        result = subprocess.run(
            [sys.executable, tmp_file],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )

        stdout = result.stdout or ""
        stderr = result.stderr or ""
        success = analyze_test_output(stdout + stderr, result.returncode)

        return {
            "success": success,
            "output": stdout,
            "error": stderr,
            "return_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": "",
            "error": "Script execution timed out after 120 seconds.",
            "return_code": -1,
        }
    except Exception as exc:
        return {"success": None, "output": "", "error": str(exc), "return_code": -1}
    finally:
        if tmp_file:
            try:
                os.unlink(tmp_file)
            except OSError:
                pass


def analyze_test_output(combined_output: str, return_code: int) -> bool:
    """
    Keyword-based pass/fail determination.

    Mirrors the LLM service keyword fallback — no LLM dependency, pure
    string matching with return-code as the final tiebreaker.
    """
    output_lower = combined_output.lower()

    success_indicators = [
        "pass:", "passed:", "test passed", "success:",
        "all tests passed", "validation successful",
        "test completed successfully", "test completed:",
        "✓", "ok -",
    ]
    failure_indicators = [
        "[error] fail", "fail:", "failed:", "test failed",
        "assertion failed", "assertionerror",
        "validation result: false", "valid: false",
        "does not display correct", "does not match expected",
        "element not found", "timeout", "exception:", "[error]",
    ]

    for indicator in success_indicators:
        if indicator in output_lower:
            return True
    for indicator in failure_indicators:
        if indicator in output_lower:
            return False

    return return_code == 0


# ===========================================================================
# Credential resolution
# ===========================================================================

def resolve_credentials(page_id: int, test_data: dict, db: Session) -> dict:
    """
    Replace {VALID_EMAIL} / {INVALID_PASSWORD} placeholders with real values
    from the test_case_credentials table.

    Returns the original dict unchanged when no placeholders are found.
    """
    if not test_data:
        return {}

    needed_keys: set = set()
    for value in test_data.values():
        if isinstance(value, str):
            m = _PLACEHOLDER_RE.fullmatch(value.strip())
            if m:
                needed_keys.add(f"{m.group(1)}_{m.group(2)}")

    if not needed_keys:
        return dict(test_data)

    rows = (
        db.query(TestCaseCredential)
        .filter(
            TestCaseCredential.page_id == page_id,
            TestCaseCredential.placeholder_key.in_(needed_keys),
        )
        .all()
    )
    cred_map: Dict[str, str] = {row.placeholder_key: row.value for row in rows}

    resolved: dict = {}
    for field, value in test_data.items():
        if isinstance(value, str):
            m = _PLACEHOLDER_RE.fullmatch(value.strip())
            if m:
                resolved[field] = cred_map.get(f"{m.group(1)}_{m.group(2)}", value)
                continue
        resolved[field] = value

    return resolved


# ===========================================================================
# Test-case payload builder
# ===========================================================================

def build_tc_payload(tc: TestCase, page: Optional[Page]) -> dict:
    """
    Build the ``__TEST_CASE__`` dict injected into the script header.

    Includes ``page_url`` and ``page_origin`` so the auth header can restore
    the session on the correct domain and pre-navigate to the right page.
    """
    tc_data = tc.data or {}
    if isinstance(tc_data, str):
        try:
            tc_data = json.loads(tc_data)
        except Exception:
            tc_data = {}

    raw_steps = tc_data.get("steps", [])
    norm_steps = []
    for s in raw_steps:
        if isinstance(s, str):
            norm_steps.append(
                re.sub(
                    r"^(Navigate|Go|Open|Visit|Launch)\s+to\s+",
                    "navigate to ",
                    s,
                    flags=re.IGNORECASE,
                )
            )
        else:
            norm_steps.append(s)

    page_url = page.page_url if page else ""
    page_origin = ""
    if page_url:
        parsed = urlparse(page_url)
        page_origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""

    return {
        "name":             tc.title,
        "steps":            norm_steps,
        "selectors":        tc_data.get("selectors", {}),
        "test_data":        tc_data.get("test_data", {}),
        "expected_outcome": tc.expected_outcome or {},
        "validation":       tc.validation or "",
        "is_valid":         tc.is_valid,
        "is_valid_default": tc.is_valid_default,
        "page_url":         page_url,
        "page_origin":      page_origin,
    }


# ===========================================================================
# Auth validation
# ===========================================================================

def validate_auth(steps: List[TestSuiteStep], scenario_map: Dict[int, TestScenario]) -> None:
    """
    Raise ``ValueError`` with a user-facing message when the suite has
    authenticated scenarios but the first step is not a login scenario.

    The exception is caught by the orchestrator and stored on
    TestSuiteExecution so the frontend can display a helpful error.
    """
    auth_required = [
        s for s in steps
        if s.scenario_id
        and scenario_map.get(s.scenario_id)
        and scenario_map[s.scenario_id].requires_auth
    ]

    if not auth_required:
        return  # No authenticated scenarios — nothing to validate

    first_scenario: Optional[TestScenario] = (
        scenario_map.get(steps[0].scenario_id)
        if steps and steps[0].scenario_id
        else None
    )

    if first_scenario is None:
        raise ValueError(
            "This test suite has authenticated scenarios but the first step has no "
            "valid scenario attached. Please add a login scenario (category: "
            "auth-positive) as the very first step."
        )

    if not _is_login_scenario(first_scenario):
        example = scenario_map[auth_required[0].scenario_id]
        raise ValueError(
            f"This test suite contains authenticated scenario(s) "
            f"(e.g. '{example.title}') but the first step "
            f"is '{first_scenario.title}' which is not a login scenario. "
            "Please select a login test case as the very first step of your "
            "test suite flow so subsequent authenticated scenarios can run correctly."
        )


# ===========================================================================
# Login execution
# ===========================================================================

def perform_login(
    login_scenario: TestScenario,
    login_step: TestSuiteStep,
    page: Optional[Page],
    db: Session,
    log: Callable[[str], None],
) -> List[dict]:
    """
    Run a targeted login to obtain an authenticated Selenium session.

    Algorithm
    ---------
    1. Select the test case to use for credentials:
       prefer is_valid_default → is_valid → first available.
    2. Resolve {VALID_EMAIL}/{VALID_PASSWORD} placeholders from the DB.
    3. Build a targeted script from TARGETED_LOGIN_SCRIPT (not scenario.script)
       to guarantee exactly one login attempt with the correct credentials.
    4. Execute the script and parse ``__AUTH_COOKIES__:{json}`` from stdout.

    Returns a list of Selenium cookie dicts; empty list when login failed.
    """
    # Parse test case IDs from the step
    tc_ids: List[int] = []
    if login_step.test_case_ids:
        try:
            tc_ids = [
                int(x.strip())
                for x in login_step.test_case_ids.split(",")
                if x.strip()
            ]
        except ValueError:
            pass

    test_cases: List[TestCase] = (
        db.query(TestCase).filter(TestCase.id.in_(tc_ids)).all() if tc_ids else []
    )

    # Pick the best login test case
    login_tc: Optional[TestCase] = (
        next((tc for tc in test_cases if tc.is_valid_default), None)
        or next((tc for tc in test_cases if tc.is_valid), None)
        or (test_cases[0] if test_cases else None)
    )

    if login_tc:
        tc_data = login_tc.data or {}
        if isinstance(tc_data, str):
            try:
                tc_data = json.loads(tc_data)
            except Exception:
                tc_data = {}

        raw_td = tc_data.get("test_data", {})
        resolved_td = resolve_credentials(page.id if page else 0, raw_td, db)

        login_payload = build_tc_payload(login_tc, page)
        login_payload["test_data"] = resolved_td
    else:
        # No test case — build a minimal payload so the script can still attempt login
        page_url = page.page_url if page else ""
        parsed = urlparse(page_url)
        login_payload = {
            "name":             login_scenario.title or "Login",
            "steps":            [],
            "selectors":        {},
            "test_data":        {},
            "expected_outcome": {},
            "validation":       "",
            "is_valid":         True,
            "is_valid_default": True,
            "page_url":         page_url,
            "page_origin":      (
                f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
            ),
        }

    header = build_script_header(login_payload, auth_cookies=None)
    login_script = header + TARGETED_LOGIN_SCRIPT + COOKIE_CAPTURE_FOOTER

    log(
        f"  Executing targeted login for tc_id={login_tc.id if login_tc else 'N/A'} "
        f"(scenario: '{login_scenario.title}') to capture session"
    )
    result = execute_test_script(login_script)

    if result["output"]:
        log(f"  stdout:\n{result['output'].rstrip()}")
    if result["error"]:
        log(f"  stderr:\n{result['error'].rstrip()}")
    log(f"  return_code={result['return_code']}  success={result['success']}")

    # Parse cookies from stdout
    auth_cookies: List[dict] = []
    for line in (result["output"] or "").splitlines():
        if line.startswith("__AUTH_COOKIES__:"):
            try:
                auth_cookies = json.loads(line[len("__AUTH_COOKIES__:"):])
                log(f"  Session captured — {len(auth_cookies)} cookie(s)")
            except Exception as exc:
                log(f"  WARNING — failed to parse auth cookies: {exc}")
            break
        if line.startswith("__AUTH_COOKIES_ERROR__:"):
            log(f"  WARNING — cookie capture error: "
                f"{line[len('__AUTH_COOKIES_ERROR__:'):]}")

    if not auth_cookies:
        log("  WARNING — no auth cookies captured; "
            "subsequent authenticated scripts may fail")

    return auth_cookies


# ===========================================================================
# TestExecution persistence
# ===========================================================================

def record_test_execution(
    db: Session,
    tc_id: int,
    step: TestSuiteStep,
    suite_id: int,
    user_id: int,
    status: str,
    logs: str,
    executed_on: datetime,
) -> None:
    """
    Upsert a TestExecution row for a single test-case result.

    Updates the existing row when one already exists for (tc_id, suite_id);
    inserts a new row otherwise.  Rolls back on flush failure so the caller's
    session stays usable.
    """
    existing = (
        db.query(TestExecution)
        .filter(
            TestExecution.test_case_id == tc_id,
            TestExecution.test_suite_id == suite_id,
        )
        .first()
    )

    if existing:
        existing.status = status
        existing.logs = (logs or "")[:65535]
        existing.executed_on = executed_on
        existing.executed_by = user_id
        existing.page_id = step.page_id
        existing.test_scenario_id = step.scenario_id
    else:
        db.add(TestExecution(
            page_id=step.page_id,
            test_scenario_id=step.scenario_id,
            test_case_id=tc_id,
            test_suite_id=suite_id,
            status=status,
            logs=(logs or "")[:65535],
            executed_on=executed_on,
            executed_by=user_id,
        ))

    try:
        db.flush()
    except Exception as exc:
        logger.warning(
            f"[SUITE_EXEC] Could not flush TestExecution for tc_id={tc_id}: {exc}"
        )
        db.rollback()


# ===========================================================================
# Main orchestrator
# ===========================================================================

def run_suite_execution(
    execution_id: int,
    suite_id: int,
    user_id: int,
    db: Session,
) -> None:
    """
    Full test-suite execution orchestrator.

    Called synchronously by the worker (inside asyncio.to_thread) so the
    event loop is never blocked.  The caller is responsible for closing the
    DB session after this function returns or raises.

    Parameters
    ----------
    execution_id : int
        PK of the TestSuiteExecution row created by the API.
    suite_id : int
        PK of the TestSuite being executed.
    user_id : int
        ID of the user who triggered the execution (for audit columns).
    db : Session
        SQLAlchemy session owned by the worker; flushed/committed here.
    """
    log_lines: List[str] = []

    # ── Logging helpers ───────────────────────────────────────────────────────

    def log(msg: str) -> None:
        entry = f"[{_ts()}] {msg}"
        log_lines.append(entry)
        logger.info(f"[SUITE_EXEC] {msg}")

    def flush_logs(execution: TestSuiteExecution) -> None:
        try:
            execution.logs = "\n".join(log_lines)
            db.commit()
        except Exception as exc:
            logger.warning(f"[SUITE_EXEC] Could not flush logs: {exc}")
            db.rollback()

    def abort(
        execution: TestSuiteExecution,
        suite: TestSuite,
        exec_status: str,
        suite_status: str,
    ) -> None:
        try:
            execution.status = exec_status
            execution.ended_at = datetime.now(timezone.utc)
            execution.logs = "\n".join(log_lines)
            suite.status = suite_status
            suite.updated_on = datetime.now(timezone.utc)
            suite.updated_by = user_id
            db.commit()
        except Exception as exc:
            logger.warning(f"[SUITE_EXEC] Could not commit abort state: {exc}")

    # ── Load execution + suite ────────────────────────────────────────────────

    execution = (
        db.query(TestSuiteExecution)
        .filter(TestSuiteExecution.id == execution_id)
        .first()
    )
    if not execution:
        logger.error(f"[SUITE_EXEC] Execution id={execution_id} not found — aborting")
        return

    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        logger.error(f"[SUITE_EXEC] Suite id={suite_id} not found — aborting")
        return

    log(f"Suite Execution Started | suite_id={suite_id}  execution_id={execution_id}")

    # ── Load steps ────────────────────────────────────────────────────────────

    steps: List[TestSuiteStep] = (
        db.query(TestSuiteStep)
        .filter(TestSuiteStep.test_suite_id == suite_id)
        .order_by(TestSuiteStep.step_order)
        .all()
    )

    if not steps:
        log("No steps found — nothing to execute.")
        abort(execution, suite, "failed", "failed")
        return

    log(f"Loaded {len(steps)} step(s)")

    # ── Load all referenced scenarios and pages in bulk ───────────────────────

    scenario_ids = [s.scenario_id for s in steps if s.scenario_id]
    scenario_map: Dict[int, TestScenario] = {
        sc.id: sc
        for sc in db.query(TestScenario).filter(TestScenario.id.in_(scenario_ids)).all()
    }

    page_ids = list({s.page_id for s in steps if s.page_id})
    page_map: Dict[int, Page] = {
        p.id: p
        for p in (db.query(Page).filter(Page.id.in_(page_ids)).all() if page_ids else [])
    }

    # ── Auth validation ───────────────────────────────────────────────────────

    try:
        validate_auth(steps, scenario_map)
        log("Auth validation passed")
    except ValueError as auth_err:
        log(f"Auth validation FAILED: {auth_err}")
        execution.execution_summary = {
            "total": 0, "passed": 0, "failed": 0, "skipped": 0,
            "error": str(auth_err),
        }
        abort(execution, suite, "error", "failed")
        return

    # ── Detect whether this suite requires authentication ─────────────────────

    needs_auth = any(
        s.scenario_id
        and scenario_map.get(s.scenario_id)
        and scenario_map[s.scenario_id].requires_auth
        for s in steps
    )

    # Auto-detect: first step is a login scenario → treat the whole suite
    # as auth even when no step has requires_auth=True explicitly.
    if not needs_auth and len(steps) > 1:
        first_sc = scenario_map.get(steps[0].scenario_id) if steps[0].scenario_id else None
        if _is_login_scenario(first_sc):
            needs_auth = True
            log("Auth auto-detected — first step is a login scenario")

    # ── Perform login and capture session cookies ─────────────────────────────

    auth_cookies: List[dict] = []

    if needs_auth:
        login_step = steps[0]
        login_scenario = (
            scenario_map.get(login_step.scenario_id) if login_step.scenario_id else None
        )
        login_page = page_map.get(login_step.page_id) if login_step.page_id else None

        log("─" * 60)
        log(
            f"Step {login_step.step_order} [LOGIN]: "
            f"scenario_id={login_step.scenario_id}  "
            f"label='{login_step.label or '—'}'"
        )

        if login_scenario:
            auth_cookies = perform_login(login_scenario, login_step, login_page, db, log)
        else:
            log("  LOGIN SKIPPED — first step has no scenario attached")

    # ── Execute each step ─────────────────────────────────────────────────────

    now = datetime.now(timezone.utc)
    summary: Dict[str, int] = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}

    for step_idx, step in enumerate(steps):
        scenario = scenario_map.get(step.scenario_id) if step.scenario_id else None
        page = page_map.get(step.page_id) if step.page_id else None
        is_first_step = step_idx == 0

        # ── Login step: already executed above; just record the result ────────
        if needs_auth and is_first_step:
            if not scenario:
                log(f"  Step {step.step_order} [LOGIN]: SKIPPED — no scenario")
                summary["skipped"] += 1
                flush_logs(execution)
                continue

            tc_ids = _parse_tc_ids(step)
            if not tc_ids:
                log(f"  Step {step.step_order} [LOGIN]: SKIPPED — no test_case_ids")
                summary["skipped"] += 1
                flush_logs(execution)
                continue

            login_status = "Passed" if auth_cookies else "Failed"
            login_log = (
                f"Login scenario '{scenario.title}' executed. "
                f"{'Session cookies captured.' if auth_cookies else 'No session cookies captured.'}"
            )
            for tc_id in tc_ids:
                summary["total"] += 1
                summary["passed" if login_status == "Passed" else "failed"] += 1
                log(f"  [{login_status.upper()}] Login test case {tc_id}")
                record_test_execution(
                    db, tc_id, step, suite_id, user_id, login_status, login_log, now
                )
            flush_logs(execution)
            continue

        # ── Normal step ───────────────────────────────────────────────────────
        log("─" * 60)
        log(
            f"Step {step.step_order}: scenario_id={step.scenario_id}  "
            f"label='{step.label or '—'}'"
        )

        if not scenario:
            log("  SKIPPED — scenario not found in DB")
            summary["skipped"] += 1
            flush_logs(execution)
            continue

        tc_ids = _parse_tc_ids(step)
        if not tc_ids:
            log("  SKIPPED — no test_case_ids for this step")
            summary["skipped"] += 1
            flush_logs(execution)
            continue

        if not scenario.script:
            log(
                f"  SKIPPED — scenario '{scenario.title}' has no script. "
                "Run the test script generation pipeline first."
            )
            for tc_id in tc_ids:
                summary["total"] += 1
                summary["skipped"] += 1
                record_test_execution(
                    db, tc_id, step, suite_id, user_id, "skipped", "No script available", now
                )
            flush_logs(execution)
            continue

        # Load test cases for this step
        test_cases: List[TestCase] = (
            db.query(TestCase).filter(TestCase.id.in_(tc_ids)).all()
        )
        tc_map: Dict[int, TestCase] = {tc.id: tc for tc in test_cases}

        # ── Auth injection decision ───────────────────────────────────────────
        #
        # FIX (Bug 1): previously cookies were only injected when
        # scenario.requires_auth=True, so non-flagged scenarios inside an
        # auth suite got a fresh unauthenticated driver and no navigation URL.
        #
        # New rule: inject cookies for ALL non-login steps when needs_auth=True
        # and cookies were captured.  The auth header:
        #   • restores the session via cookie injection,
        #   • pre-navigates to page.page_url (Step 5),
        #   • sets __COOKIES_AUTH_DONE__ = True to suppress redundant blocks.
        step_is_login = _is_login_scenario(scenario)
        step_auth = (
            auth_cookies
            if (needs_auth and auth_cookies and not step_is_login)
            else None
        )

        # Warn early when page_url is missing — Step 5 in the header will be
        # a no-op and the script may still crash looking for a URL.
        if step_auth and (not page or not page.page_url):
            log(
                f"  WARNING — step {step.step_order} has no page_url "
                f"(page_id={step.page_id}). Auth header will skip navigation. "
                "Ensure the Page record has a valid page_url set."
            )

        log(
            f"  Running '{scenario.title}' | "
            f"{len(tc_ids)} test case(s) | "
            f"auth={'yes' if step_auth else 'no'}"
        )

        # ── Run the scenario script once per step ─────────────────────────────
        try:
            # Prefer is_valid_default → is_valid → first
            payload_tc = (
                next((tc for tc in test_cases if tc.is_valid_default), None)
                or next((tc for tc in test_cases if tc.is_valid), None)
                or (test_cases[0] if test_cases else None)
            )

            if payload_tc is None:
                log("  SKIPPED — no test cases found in DB for this step")
                for tc_id in tc_ids:
                    summary["total"] += 1
                    summary["skipped"] += 1
                    record_test_execution(
                        db, tc_id, step, suite_id, user_id,
                        "skipped", "Test case not found", now
                    )
                flush_logs(execution)
                continue

            tc_data = payload_tc.data or {}
            if isinstance(tc_data, str):
                try:
                    tc_data = json.loads(tc_data)
                except Exception:
                    tc_data = {}

            resolved_td = resolve_credentials(
                step.page_id or 0,
                tc_data.get("test_data", {}),
                db,
            )

            tc_payload = build_tc_payload(payload_tc, page)
            tc_payload["test_data"] = resolved_td

            header = build_script_header(tc_payload, step_auth)
            full_script = header + scenario.script

            result = execute_test_script(full_script)

            if result["output"]:
                log(f"  stdout:\n{result['output'].rstrip()}")
            if result["error"]:
                log(f"  stderr:\n{result['error'].rstrip()}")
            log(f"  return_code={result['return_code']}  success={result['success']}")

            exec_log = (result["output"] or "") + (
                "\n" + result["error"] if result["error"] else ""
            )

            # Record result for every tc_id associated with this step
            for tc_id in tc_ids:
                summary["total"] += 1
                tc = tc_map.get(tc_id)
                tc_title = tc.title if tc else f"tc_id={tc_id}"

                if result["success"]:
                    summary["passed"] += 1
                    tc_status = "Passed"
                else:
                    summary["failed"] += 1
                    tc_status = "Failed"

                log(f"  [{tc_status.upper()}] tc_id={tc_id} '{tc_title}'")
                record_test_execution(
                    db, tc_id, step, suite_id, user_id, tc_status, exec_log, now
                )

        except Exception as step_exc:
            logger.error(
                f"[SUITE_EXEC] Error running step {step.step_order}: {step_exc}"
            )
            log(f"  [ERROR] Step {step.step_order}: {step_exc}")
            for tc_id in tc_ids:
                summary["total"] += 1
                summary["failed"] += 1
                record_test_execution(
                    db, tc_id, step, suite_id, user_id, "Failed", str(step_exc), now
                )

        flush_logs(execution)

    # ── Compute and persist final status ──────────────────────────────────────

    log("─" * 60)
    log(
        f"Execution complete | total={summary['total']}  "
        f"passed={summary['passed']}  failed={summary['failed']}  "
        f"skipped={summary['skipped']}"
    )

    runnable = summary["total"] - summary["skipped"]
    if runnable == 0 or summary["failed"] == runnable:
        exec_status, suite_status = "failed", "failed"
    elif summary["failed"] == 0:
        exec_status, suite_status = "passed", "done"
    else:
        exec_status, suite_status = "partially_passed", "failed"

    log(f"Final status → execution={exec_status}  suite={suite_status}")

    execution.status = exec_status
    execution.ended_at = datetime.now(timezone.utc)
    execution.execution_summary = summary
    execution.logs = "\n".join(log_lines)

    suite.status = suite_status
    suite.updated_on = datetime.now(timezone.utc)
    suite.updated_by = user_id

    db.commit()
    logger.info(
        f"[SUITE_EXEC] Done | execution_id={execution_id}  "
        f"status={exec_status}  summary={summary}"
    )