"""Worker for test suite execution.

Consumes TEST_SUITE_EXECUTION_QUEUE messages and orchestrates:

  1. Auth validation
       - If any step's scenario has requires_auth=True, the very first step
         MUST be a login scenario (category auth-positive/auth-negative or
         title contains "login").
       - If auth is required but no login step is present → execution aborted
         with a clear error message surfaced to the frontend.

  2. Login execution (auth suites only)
       - Runs the first step's scenario script with COOKIE_CAPTURE_FOOTER
         appended to capture the Selenium session cookies.
       - Credentials are resolved from test_case.data["test_data"] via the
         TestCaseCredential table (same as test_execution_service.py).
       - The __TEST_CASE__ block is injected into the script header so the
         login script receives real, resolved credentials.

  3. Step execution
       - Each step is executed in step_order.
       - For each test case, _build_script_header(tc_payload, auth_cookies)
         prepends the __TEST_CASE__ injection block and—when auth cookies are
         present—the full cookie-restoration + driver monkey-patch block so
         the script's own get_driver() returns the authenticated driver.
       - Scripts execute in a subprocess with PYTHONPATH pointing at the
         LLM service directory (where app.services.selenium_driver lives).

  4. Result tracking
       - One TestExecution row per test case per step.
       - Timestamped log entries accumulated in TestSuiteExecution.logs.

  5. Status update
       - TestSuiteExecution and TestSuite statuses set on completion.

Status values
-------------
  passed           : every runnable test case passed
  partially_passed : at least one passed and at least one failed
  failed           : all runnable test cases failed (or zero runnable)
  error            : validation error or unexpected exception

TestSuite.status after execution
----------------------------------
  passed              → "done"
  partially_passed    → "failed"
  failed / error      → "failed"
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.config.logger import logger
from app.config.setting import settings
from shared_orm.models.page import Page
from shared_orm.models.test_case import TestCase
from shared_orm.models.test_case_credential import TestCaseCredential
from shared_orm.models.test_execution import TestExecution
from shared_orm.models.test_scenario import TestScenario
from shared_orm.models.test_suite import TestSuite
from shared_orm.models.test_suite_execution import TestSuiteExecution
from shared_orm.models.test_suite_step import TestSuiteStep
# ---------------------------------------------------------------------------
# Cookie capture — appended to the login script so the authenticated
# browser's session cookies are printed to stdout for capture.
# ---------------------------------------------------------------------------

COOKIE_CAPTURE_FOOTER = """
import json as _cookie_json
try:
    _captured_cookies = driver.get_cookies()
    print(f"__AUTH_COOKIES__:{_cookie_json.dumps(_captured_cookies)}")
except Exception as _cookie_err:
    print(f"__AUTH_COOKIES_ERROR__:{_cookie_err}")
"""

# Placeholder pattern used in test_data: {VALID_EMAIL}, {INVALID_PASSWORD}
_PLACEHOLDER_RE = re.compile(r"\{(VALID|INVALID)_([A-Z_]+)\}")


# ---------------------------------------------------------------------------
# Timestamp helper
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# ---------------------------------------------------------------------------
# Script header builder
# Ported from LLM service test_execution_service.py._build_script_header
# ---------------------------------------------------------------------------

def _build_script_header(tc_payload: dict, auth_cookies: list = None) -> str:
    """
    Build the Python source block prepended to every generated scenario script.

    Without auth_cookies:
        Injects __TEST_CASE__ and initialises a fresh Selenium driver.

    With auth_cookies:
        Injects __TEST_CASE__, then:
          1. Creates a fresh driver.
          2. Navigates to the site origin (so the domain accepts cookies).
          3. Injects every session cookie.
          4. Refreshes so the server sees the restored session.
          5. Monkey-patches sys.modules so the script's get_driver() call
             returns this already-authenticated driver — without the patch
             the script would discard the session by opening a new driver.
          6. Sets __COOKIES_AUTH_DONE__ = True so any leftover login blocks
             in the generated script skip themselves gracefully.
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
            "# Step 6: suppress redundant login blocks in already-generated scripts",
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


# ---------------------------------------------------------------------------
# Script execution
# Follows the pattern from LLM service test_execution_service.execute_test_script()
# ---------------------------------------------------------------------------

def _execute_test_script(script: str) -> dict:
    """
    Write script to a temp file and run it via subprocess.

    Sets PYTHONPATH to LLM_SERVICE_DIR (from settings) so that
    `from app.services.selenium_driver import get_driver` resolves
    inside the spawned process — same as test_execution_service.py which
    uses env["PYTHONPATH"] = os.getcwd() inside the LLM service container.

    Returns:
        {
            "success":     bool | None,  # None = timeout / exception
            "output":      str,          # stdout
            "error":       str,          # stderr
            "return_code": int,
        }
    """
    tmp_file = None
    try:
        if not script.strip():
            return {"success": None, "output": "", "error": "Empty script", "return_code": -1}

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(script)
            tmp_file = f.name

        env = os.environ.copy()
        llm_service_dir = getattr(settings, "LLM_SERVICE_DIR", "")
        if llm_service_dir and os.path.isdir(llm_service_dir):
            existing = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = (
                f"{llm_service_dir}{os.pathsep}{existing}" if existing else llm_service_dir
            )
        else:
            # Fallback: use cwd (works when worker runs in LLM service container)
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
        success = _analyze_test_output(stdout + stderr, result.returncode)

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


def _analyze_test_output(combined_output: str, return_code: int) -> bool:
    """
    Keyword-based pass/fail determination (mirrors LLM service keyword fallback).
    No LLM dependency — pure string matching + return code.
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


# ---------------------------------------------------------------------------
# Credential resolution
# DB-only — resolves {VALID_EMAIL} / {INVALID_PASSWORD} placeholders from
# the test_case_credentials table (same store used by TestCredentialService).
# ---------------------------------------------------------------------------

def _resolve_credentials(page_id: int, test_data: dict, db: Session) -> dict:
    """Replace credential placeholders with values from test_case_credentials."""
    if not test_data:
        return {}

    needed_keys = set()
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
    cred_map = {row.placeholder_key: row.value for row in rows}

    resolved = {}
    for field, value in test_data.items():
        if isinstance(value, str):
            m = _PLACEHOLDER_RE.fullmatch(value.strip())
            if m:
                resolved[field] = cred_map.get(f"{m.group(1)}_{m.group(2)}", value)
                continue
        resolved[field] = value

    return resolved


# ---------------------------------------------------------------------------
# Test case payload builder
# Mirrors tc_payload format used in test_execution_service.py._execute_scenario
# ---------------------------------------------------------------------------

def _build_tc_payload(tc: TestCase, page: Optional[Page]) -> dict:
    """
    Build the __TEST_CASE__ dict injected into the script header at runtime.
    Includes page_url and page_origin so the auth header can restore the
    session on the correct domain.
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


# ---------------------------------------------------------------------------
# Auth validation
# ---------------------------------------------------------------------------

def _validate_auth(steps: list, scenario_map: dict) -> None:
    """
    Raise ValueError with a user-facing message when:
      • Any step's scenario has requires_auth=True
      • AND the first step is not a login scenario.

    The error is stored on TestSuiteExecution and surfaced to the frontend
    so the user knows to add a login scenario at the top of the flow.
    """
    auth_required = [
        s for s in steps
        if s.scenario_id
        and scenario_map.get(s.scenario_id)
        and scenario_map[s.scenario_id].requires_auth
    ]

    if not auth_required:
        return  # No authenticated scenarios — no validation needed

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

    is_login = (
        (first_scenario.category or "") in ("auth-positive", "auth-negative")
        or "login" in (first_scenario.title or "").lower()
    )

    if not is_login:
        example = scenario_map[auth_required[0].scenario_id]
        raise ValueError(
            f"This test suite contains authenticated scenario(s) "
            f"(e.g. '{example.title}') but the first step "
            f"is '{first_scenario.title}' which is not a login scenario. "
            "Please select a login test case as the very first step of your "
            "test suite flow so subsequent authenticated scenarios can run correctly."
        )


# ---------------------------------------------------------------------------
# Login step execution with cookie capture
# ---------------------------------------------------------------------------

def _perform_login(
    login_scenario: TestScenario,
    login_step: TestSuiteStep,
    page: Optional[Page],
    db: Session,
    log,
) -> List[dict]:
    """
    Run the login scenario's script to obtain an authenticated Selenium session.

    1. Picks the default-valid test case (is_valid_default=True) for credentials.
       Falls back to the first valid test case if none is marked default.
    2. Resolves {VALID_EMAIL}/{VALID_PASSWORD} placeholders from the DB.
    3. Injects resolved credentials via _build_script_header (as __TEST_CASE__).
    4. Appends COOKIE_CAPTURE_FOOTER so the subprocess prints the session cookies.
    5. Parses __AUTH_COOKIES__:{json} from stdout.

    Returns a list of Selenium cookie dicts (empty if login failed or no cookies).
    """
    if not login_scenario.script:
        log("  LOGIN SKIPPED — login scenario has no script")
        return []

    # Resolve the login test case IDs from the step
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

    # Load test cases for this step
    test_cases: List[TestCase] = (
        db.query(TestCase).filter(TestCase.id.in_(tc_ids)).all()
        if tc_ids else []
    )

    # Prefer is_valid_default test case (the canonical positive case with real creds)
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
        resolved_td = _resolve_credentials(page.id if page else 0, raw_td, db)

        login_payload = _build_tc_payload(login_tc, page)
        login_payload["test_data"] = resolved_td  # inject resolved credentials
    else:
        # No test case found — build a minimal payload; script may still run
        page_url = page.page_url if page else ""
        parsed = urlparse(page_url)
        login_payload = {
            "name": login_scenario.title or "Login",
            "steps": [],
            "selectors": {},
            "test_data": {},
            "expected_outcome": {},
            "validation": "",
            "is_valid": True,
            "is_valid_default": True,
            "page_url": page_url,
            "page_origin": (
                f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else ""
            ),
        }

    # Build the full login script: header (no auth cookies yet) + scenario script + cookie footer
    header = _build_script_header(login_payload, auth_cookies=None)
    login_script = header + login_scenario.script + COOKIE_CAPTURE_FOOTER

    log(f"  Executing login scenario '{login_scenario.title}' to capture session")
    result = _execute_test_script(login_script)

    if result["output"]:
        log(f"  stdout:\n{result['output'].rstrip()}")
    if result["error"]:
        log(f"  stderr:\n{result['error'].rstrip()}")
    log(f"  return_code={result['return_code']}  success={result['success']}")

    # Parse auth cookies from stdout
    auth_cookies: List[dict] = []
    for line in (result["output"] or "").splitlines():
        if line.startswith("__AUTH_COOKIES__:"):
            try:
                auth_cookies = json.loads(line[len("__AUTH_COOKIES__:"):])
                log(f"  Session captured — {len(auth_cookies)} cookie(s)")
            except Exception as e:
                log(f"  WARNING — failed to parse auth cookies: {e}")
            break
        if line.startswith("__AUTH_COOKIES_ERROR__:"):
            log(f"  WARNING — cookie capture error: {line[len('__AUTH_COOKIES_ERROR__:'):]}")

    if not auth_cookies:
        log("  WARNING — no auth cookies captured; subsequent authenticated scripts may fail")

    return auth_cookies


# ---------------------------------------------------------------------------
# TestExecution record helper
# ---------------------------------------------------------------------------

def _record_test_execution(
    db: Session,
    tc_id: int,
    step: TestSuiteStep,
    suite_id: int,
    user_id: int,
    status: str,
    logs: str,
    executed_on: datetime,
) -> None:
    """Upsert a TestExecution row for a single test case result."""
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
        logger.warning(f"[SUITE_EXEC] Could not flush TestExecution for tc_id={tc_id}: {exc}")
        db.rollback()


# ---------------------------------------------------------------------------
# Main synchronous execution runner
# ---------------------------------------------------------------------------

def _run_execution_sync(execution_id: int, suite_id: int, user_id: int) -> None:
    """
    Full test suite execution orchestrator.
    Runs synchronously inside asyncio.to_thread so the event loop is not blocked.
    """
    db: Session = SessionLocal()
    log_lines: List[str] = []

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

    def abort(execution: TestSuiteExecution, suite: TestSuite,
              exec_status: str, suite_status: str) -> None:
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

    try:
        # ── Load execution + suite ────────────────────────────────────────────
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

        # ── Load steps in step_order ──────────────────────────────────────────
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

        # ── Load all referenced scenarios ─────────────────────────────────────
        scenario_ids = [s.scenario_id for s in steps if s.scenario_id]
        scenario_map: Dict[int, TestScenario] = {
            sc.id: sc
            for sc in db.query(TestScenario).filter(TestScenario.id.in_(scenario_ids)).all()
        }

        # ── Load all referenced pages ─────────────────────────────────────────
        page_ids = list({s.page_id for s in steps if s.page_id})
        page_map: Dict[int, Page] = {
            p.id: p
            for p in (db.query(Page).filter(Page.id.in_(page_ids)).all() if page_ids else [])
        }

        # ── Auth validation ───────────────────────────────────────────────────
        try:
            _validate_auth(steps, scenario_map)
            log("Auth validation passed")
        except ValueError as auth_err:
            log(f"Auth validation FAILED: {auth_err}")
            execution.execution_summary = {
                "total": 0, "passed": 0, "failed": 0, "skipped": 0,
                "error": str(auth_err),
            }
            abort(execution, suite, "error", "failed")
            return

        # ── Determine whether this suite needs authentication ─────────────────
        needs_auth = any(
            s.scenario_id
            and scenario_map.get(s.scenario_id)
            and scenario_map[s.scenario_id].requires_auth
            for s in steps
        )

        # ── Perform login and capture session cookies (auth suites only) ──────
        auth_cookies: List[dict] = []

        if needs_auth:
            login_step = steps[0]
            login_scenario = scenario_map.get(login_step.scenario_id) if login_step.scenario_id else None
            login_page = page_map.get(login_step.page_id) if login_step.page_id else None

            log("─" * 60)
            log(
                f"Step {login_step.step_order} [LOGIN]: "
                f"scenario_id={login_step.scenario_id}  "
                f"label='{login_step.label or '—'}'"
            )

            if login_scenario:
                auth_cookies = _perform_login(
                    login_scenario, login_step, login_page, db, log
                )
            else:
                log("  LOGIN SKIPPED — first step has no scenario attached")

        # ── Execute each step in order ────────────────────────────────────────
        now = datetime.now(timezone.utc)
        summary = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}

        for step_idx, step in enumerate(steps):
            scenario = scenario_map.get(step.scenario_id) if step.scenario_id else None
            page = page_map.get(step.page_id) if step.page_id else None
            is_first_step = step_idx == 0

            # The login step (step 0 in auth suites) was already executed above;
            # we only need to record its results, not re-run the script.
            if needs_auth and is_first_step:
                # Record login step result from the execution we already ran
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

                # Login result: passed if cookies captured, failed otherwise
                login_status = "Passed" if auth_cookies else "Failed"
                login_log = (
                    f"Login scenario '{scenario.title}' executed. "
                    f"{'Session cookies captured.' if auth_cookies else 'No session cookies captured.'}"
                )
                for tc_id in tc_ids:
                    summary["total"] += 1
                    if login_status == "Passed":
                        summary["passed"] += 1
                    else:
                        summary["failed"] += 1
                    log(f"  [{login_status.upper()}] Login test case {tc_id}")
                    _record_test_execution(
                        db, tc_id, step, suite_id, user_id, login_status, login_log, now
                    )
                flush_logs(execution)
                continue

            # ── Normal step ───────────────────────────────────────────────────
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
                    _record_test_execution(
                        db, tc_id, step, suite_id, user_id, "skipped", "No script available", now
                    )
                flush_logs(execution)
                continue

            # ── Load test cases for this step ─────────────────────────────────
            tc_map: Dict[int, TestCase] = {
                tc.id: tc
                for tc in db.query(TestCase).filter(TestCase.id.in_(tc_ids)).all()
            }

            # ── Inject auth cookies for authenticated scenarios ────────────────
            step_auth = auth_cookies if scenario.requires_auth else None

            log(
                f"  Running '{scenario.title}' | "
                f"{len(tc_ids)} test case(s) | "
                f"auth={'yes' if step_auth else 'no'}"
            )

            # ── Execute one script per test case (dynamic __TEST_CASE__ injection)
            for tc_id in tc_ids:
                summary["total"] += 1
                tc = tc_map.get(tc_id)

                if tc is None:
                    log(f"  [SKIP] tc_id={tc_id} — not found in DB")
                    summary["skipped"] += 1
                    summary["total"] -= 1
                    continue

                try:
                    # Resolve credentials for this test case
                    tc_data = tc.data or {}
                    if isinstance(tc_data, str):
                        try:
                            tc_data = json.loads(tc_data)
                        except Exception:
                            tc_data = {}

                    resolved_td = _resolve_credentials(
                        step.page_id or 0,
                        tc_data.get("test_data", {}),
                        db,
                    )

                    # Build tc_payload and override test_data with resolved values
                    tc_payload = _build_tc_payload(tc, page)
                    tc_payload["test_data"] = resolved_td

                    # Prepend header (with optional auth cookie restoration)
                    header = _build_script_header(tc_payload, step_auth)
                    full_script = header + scenario.script

                    result = _execute_test_script(full_script)

                    if result["output"]:
                        log(f"  stdout:\n{result['output'].rstrip()}")
                    if result["error"]:
                        log(f"  stderr:\n{result['error'].rstrip()}")
                    log(f"  return_code={result['return_code']}  success={result['success']}")

                    exec_log = (result["output"] or "") + (
                        "\n" + result["error"] if result["error"] else ""
                    )

                    if result["success"]:
                        summary["passed"] += 1
                        tc_status = "Passed"
                    else:
                        summary["failed"] += 1
                        tc_status = "Failed"

                    log(f"  [{tc_status.upper()}] tc_id={tc_id} '{tc.title}'")
                    _record_test_execution(
                        db, tc_id, step, suite_id, user_id, tc_status, exec_log, now
                    )

                except Exception as tc_exc:
                    logger.error(f"[SUITE_EXEC] Error running tc_id={tc_id}: {tc_exc}")
                    log(f"  [ERROR] tc_id={tc_id}: {tc_exc}")
                    summary["failed"] += 1
                    _record_test_execution(
                        db, tc_id, step, suite_id, user_id, "Failed", str(tc_exc), now
                    )

            flush_logs(execution)

        # ── Compute final status ──────────────────────────────────────────────
        log("─" * 60)
        log(
            f"Execution complete | total={summary['total']}  "
            f"passed={summary['passed']}  failed={summary['failed']}  "
            f"skipped={summary['skipped']}"
        )

        runnable = summary["total"] - summary["skipped"]
        if runnable == 0 or summary["failed"] == runnable:
            # All runnable test cases failed (or nothing ran)
            exec_status = "failed"
            suite_status = "failed"
        elif summary["failed"] == 0:
            # Every runnable test case passed
            exec_status = "passed"
            suite_status = "done"
        else:
            # Some passed, some failed
            exec_status = "partially_passed"
            suite_status = "failed"

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

    except Exception as exc:
        logger.exception(f"[SUITE_EXEC] Unexpected error in execution_id={execution_id}: {exc}")
        log_lines.append(f"[{_ts()}] FATAL ERROR: {exc}")
        try:
            execution = (
                db.query(TestSuiteExecution)
                .filter(TestSuiteExecution.id == execution_id)
                .first()
            )
            suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
            if execution:
                execution.status = "error"
                execution.ended_at = datetime.now(timezone.utc)
                execution.logs = "\n".join(log_lines)
            if suite:
                suite.status = "failed"
                suite.updated_on = datetime.now(timezone.utc)
                suite.updated_by = user_id
            db.commit()
        except Exception as save_exc:
            logger.exception(f"[SUITE_EXEC] Could not save error state: {save_exc}")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def _parse_tc_ids(step: TestSuiteStep) -> List[int]:
    """Parse comma-separated test_case_ids string into a list of ints."""
    if not step.test_case_ids:
        return []
    try:
        return [int(x.strip()) for x in step.test_case_ids.split(",") if x.strip()]
    except ValueError:
        logger.warning(f"[SUITE_EXEC] Malformed test_case_ids on step {step.id}: {step.test_case_ids!r}")
        return []


# ---------------------------------------------------------------------------
# Async RabbitMQ handler
# ---------------------------------------------------------------------------

class TestSuiteExecutionWorker:

    async def process_test_suite_execution(
        self,
        message: Union[bytes, str, Dict],
    ) -> None:
        """RabbitMQ message handler for TEST_SUITE_EXECUTION_QUEUE."""
        try:
            if isinstance(message, (bytes, bytearray)):
                body: Dict = json.loads(message.decode("utf-8"))
            elif isinstance(message, str):
                body = json.loads(message)
            else:
                body = message

            execution_id: Optional[int] = body.get("execution_id")
            suite_id: Optional[int] = body.get("suite_id")
            user_id: int = body.get("user_id", 0)

            if not execution_id or not suite_id:
                logger.error(
                    f"[SUITE_EXEC_WORKER] Invalid message — "
                    f"execution_id or suite_id missing: {body}"
                )
                return

            logger.info(
                f"[SUITE_EXEC_WORKER] Received | "
                f"execution_id={execution_id}  suite_id={suite_id}  user_id={user_id}"
            )

            await asyncio.to_thread(
                _run_execution_sync, execution_id, suite_id, user_id
            )

        except json.JSONDecodeError:
            logger.exception("[SUITE_EXEC_WORKER] Failed to decode message JSON")
        except Exception as exc:
            logger.exception(f"[SUITE_EXEC_WORKER] Unhandled error: {exc}")


test_suite_execution_worker = TestSuiteExecutionWorker()
