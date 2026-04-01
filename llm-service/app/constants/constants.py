"""Site extraction filtering constants.

Defines file extensions and path fragments that the page extractor should
ignore. Keep these lists small and explicit — they are used to quickly
skip binary, media, or asset endpoints that are not useful for text
analysis.
"""
import re
# File extensions that indicate binary, media, archive or other non-HTML
# resources. The extractor should skip URLs that end with these extensions.
BLOCKED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".pdf",
    ".txt",
    ".csv",
    ".json",
    ".xml",
    ".zip",
    ".rar",
    ".7z",
    ".mp4",
    ".webm",
    ".avi",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".bin",
}


# Path substrings commonly present in asset, upload or download endpoints.
# If a URL contains any of these fragments, it is usually safe to skip it
# during crawl/page extraction to avoid non-content pages.
BLOCKED_PATH_KEYWORDS = {
    "/download/",
    "/uploads/",
    "/files/",
    "/assets/",
    "/static/",
    "/media/",
}



# ---------------------------------------------------------------------------
# Cookie capture footer
# Appended to the login script so the authenticated browser's session
# cookies are printed to stdout for capture.
# ---------------------------------------------------------------------------

COOKIE_CAPTURE_FOOTER = """
import json as _cookie_json
try:
    _captured_cookies = driver.get_cookies()
    print(f"__AUTH_COOKIES__:{_cookie_json.dumps(_captured_cookies)}")
except Exception as _cookie_err:
    print(f"__AUTH_COOKIES_ERROR__:{_cookie_err}")
"""

# ---------------------------------------------------------------------------
# Targeted login script template
# Driven entirely by __TEST_CASE__ (injected via _build_script_header).
# We deliberately do NOT use scenario.script because old-style scripts
# hardcode all test cases — including invalid-credential ones — and leave
# the browser in an unauthenticated state before cookie capture.
# ---------------------------------------------------------------------------

TARGETED_LOGIN_SCRIPT = """
import time as _login_time
from selenium.webdriver.common.by import By as _By
from selenium.webdriver.support.ui import WebDriverWait as _WDW2
from selenium.webdriver.support import expected_conditions as _EC2

_tc    = __TEST_CASE__
_sels  = _tc.get("selectors", {})
_tdata = _tc.get("test_data", {})
_purl  = _tc.get("page_url", "")

# Navigate to login page
if _purl:
    driver.get(_purl)
    try:
        _WDW2(driver, 15).until(lambda d: d.execute_script('return document.readyState') == 'complete')
    except Exception:
        pass

def _find_el(sel):
    \"\"\"Try CSS then XPath.\"\"\"
    for _by in (_By.CSS_SELECTOR, _By.XPATH):
        try:
            return _WDW2(driver, 10).until(_EC2.presence_of_element_located((_by, sel)))
        except Exception:
            continue
    return None

# Resolve selectors — support multiple naming conventions
_user_sel = (
    _sels.get("username") or _sels.get("username_selector") or
    _sels.get("email")    or _sels.get("email_selector")    or
    _sels.get("user")
)
_pass_sel = (
    _sels.get("password") or _sels.get("password_selector") or
    _sels.get("pass")
)
_sub_sel = (
    _sels.get("submit")        or _sels.get("submit_selector") or
    _sels.get("submit_button") or _sels.get("login_button")    or
    _sels.get("button")
)

# Resolve credentials — support multiple naming conventions
_username_val = None
_password_val = None
for _k, _v in _tdata.items():
    _kl = _k.lower()
    if any(x in _kl for x in ("email", "username", "user", "login", "name")):
        _username_val = _v
    elif any(x in _kl for x in ("password", "pass", "pwd", "secret")):
        _password_val = _v

# Fallback: use the first two values in order
if not _username_val or not _password_val:
    _vals = list(_tdata.values())
    if not _username_val and _vals:
        _username_val = _vals[0]
    if not _password_val and len(_vals) > 1:
        _password_val = _vals[1]

# Fill username
if _user_sel and _username_val:
    _uf = _find_el(_user_sel)
    if _uf:
        _uf.clear()
        _uf.send_keys(str(_username_val))
    else:
        print(f"[ERROR] Username field not found with selector: {_user_sel}")
else:
    print(f"[WARN] Username selector or value missing: sel={_user_sel!r} val={_username_val!r}")

# Fill password
if _pass_sel and _password_val:
    _pf = _find_el(_pass_sel)
    if _pf:
        _pf.clear()
        _pf.send_keys(str(_password_val))
    else:
        print(f"[ERROR] Password field not found with selector: {_pass_sel}")
else:
    print(f"[WARN] Password selector or value missing: sel={_pass_sel!r} val={_password_val!r}")

# Submit
if _sub_sel:
    _sb = _find_el(_sub_sel)
    if _sb:
        _prev_url = driver.current_url
        _sb.click()
        _login_time.sleep(3)
        if driver.current_url != _prev_url:
            print("Test Completed: Login successful")
        else:
            print("[ERROR] Login failed: URL did not change after login")
    else:
        print(f"[ERROR] Submit button not found with selector: {_sub_sel}")
else:
    print("[WARN] No submit selector found — attempting Enter key on password field")
    if _pass_sel:
        _pf2 = _find_el(_pass_sel)
        if _pf2:
            from selenium.webdriver.common.keys import Keys as _Keys
            _prev_url = driver.current_url
            _pf2.send_keys(_Keys.RETURN)
            _login_time.sleep(3)
            if driver.current_url != _prev_url:
                print("Test Completed: Login successful via Enter key")
            else:
                print("[ERROR] Login failed: URL did not change after Enter key")
"""

# Placeholder pattern used in test_data: {VALID_EMAIL}, {INVALID_PASSWORD}
_PLACEHOLDER_RE = re.compile(r"\{(VALID|INVALID)_([A-Z_]+)\}")

