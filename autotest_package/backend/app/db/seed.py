from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.role import Role
from app.models.user import User
from app.core.config import settings
from app.core.security import hash_password
from pathlib import Path

# NEW imports for settings seeding
from app.models.setting import Setting, SettingTypeEnum

ADMIN_ACCESS = {
    "modules": ["role","user","settings","profile","site","page","test_scenario","test_case","test_suite","test_config","test_schedule"]
}
USER_ACCESS = {
    "modules": ["profile","site","page","test_scenario","test_case","test_config","test_suite","test_schedule"]
}

def seed_roles(db: Session):
    # role 1: Admin
    admin = db.execute(select(Role).where(Role.id == 1)).scalar_one_or_none()
    if not admin:
        admin = Role(id=1, type="Administrator", access=ADMIN_ACCESS)
        db.add(admin)
    else:
        admin.type = "Administrator"
        admin.access = ADMIN_ACCESS
    # role 2: User
    user = db.execute(select(Role).where(Role.id == 2)).scalar_one_or_none()
    if not user:
        user = Role(id=2, type="User", access=USER_ACCESS)
        db.add(user)
    else:
        user.type = "User"
        user.access = USER_ACCESS
    db.commit()

def seed_admin_user(db: Session):
    admin_user = db.execute(select(User).where(User.username == settings.ADMIN_USERNAME)).scalar_one_or_none()
    if not admin_user:
        admin_user = User(
            role_id=1,
            username=settings.ADMIN_USERNAME,
            password=hash_password(settings.ADMIN_PASSWORD),
            name=settings.ADMIN_NAME,
            email=settings.ADMIN_EMAIL,
            is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

# ---- NEW: settings seeder ----

# Map sheet "Type" strings to SettingTypeEnum values
_TYPE_NORMALIZE = {
    "Text": "Text",
    "Number": "Number",
    "Date": "Date",
    "Dropdown": "Dropdown",
    "Drop-down": "Dropdown",  # tolerate sheet variation
    "Radio Button": "Radio Button",
    "Checkbox": "Checkbox",
}

# Paste the seed rows from Seed-Data-Setting.xlsx (sheet: Setting Seed)
# Columns per sheet: ID | Key | Titile | Description | Type | possible_values | default_value | actual_value
# Note: The sheet’s column name “Titile” has a typo; we read as title.
_SETTING_SEED_ROWS = [
    # id, key, title, description, type, possible_values, default_value, actual_value
    (1,  "general-setting: API KEY- OpenAI",         "OpenAI API Key",                 "",        "Text",      "",                                                "",                         ""),
    (2,  "general-setting: API KEY- Groq",           "Groq API Key",                   "",        "Text",      "",                                                "",                         ""),
    (3,  "general-setting: API KEY- Google",         "Google API Key",                 "",        "Text",      "",                                                "",                         ""),
    (4,  "general-setting: API KEY- Anthropic",      "Anthropic API Key",              "",        "Text",      "",                                                "",                         ""),
    (5,  "general-setting: LOG-LEVEL",               "Log-Level",                      "",        "Dropdown",  "DEBUG, INFO, WARNING, ERROR, CRITICAL",           "DEBUG",                   "DEBUG"),
    (6,  "general-setting: TESTING-FRAMEWORK",       "Testing-framework",              "",        "Dropdown",  "Selenium",                                         "Selenium",                "Selenium"),
    (7,  "general-setting: CODING-LANGUAGE",         "Coding-language",                "",        "Dropdown",  "Python",                                           "Python",                  "Python"),
    (8,  "general-setting: MAX-DEPTH",               "Max-Depth",                      "",        "Number",    "1,2,3,4,5....",                                   "1",                       "1"),
    (9,  "general-setting: WAIT-TIME",               "Custom Wait-Time",               "",        "Text",      "",                                                "2 minutes (120 seconds)", "2 minutes (120 seconds)"),
    (10, "Prompt-setting: PROMPT",                   "Prompt",                         "",        "Text",      "",                                                "",                         ""),
    (11, "LLM-setting: MODEL-PROVIDER",              "Model Provider",                 "",        "Radio Button", "OpenAI, Groq, Google-Gemini, Anthropic, Ollama", "OpenAI",                 "OpenAI"),
    (12, "LLM-setting: ANALYSIS-MODEL-OPENAI",       "Analysis Model",                 "",        "Text",      "",                                                "gpt-4.1-mini-2025-04-14", "gpt-4.1-mini-2025-04-14"),
    (13, "LLM-setting: SELENIUM-MODEL-OPENAI",       "Selenium Model",                 "",        "Text",      "",                                                "gpt-4.1-2025-04-14",      "gpt-4.1-2025-04-14"),
    (14, "LLM-setting: RESULT-ANALYSIS-MODEL-OPENAI","Result Analysis Model",          "",        "Text",      "",                                                "gpt-5-mini-2025-08-07",   "gpt-5-mini-2025-08-07"),
    (15, "LLM-setting: TEMPERATURE-OPENAI",          "Temperature",                    "",        "Number",    "",                                                "0.2",                     "0.2"),
    (16, "LLM-setting: ANALYSIS-MODEL-GROQ",         "Analysis Model",                 "",        "Text",      "",                                                "meta-llama/llama-4-scout-17b-16e-instruct", "meta-llama/llama-4-scout-17b-16e-instruct"),
    (17, "LLM-setting: SELENIUM-MODEL-GROQ",         "Selenium Model",                 "",        "Text",      "",                                                "meta-llama/llama-4-maverick-17b-128e-instruct", "meta-llama/llama-4-maverick-17b-128e-instruct"),
    (18, "LLM-setting: RESULT-ANALYSIS-MODEL-GROQ",  "Result Analysis Model",          "",        "Text",      "",                                                "meta-llama/llama-4-scout-17b-16e-instruct", "meta-llama/llama-4-scout-17b-16e-instruct"),
    (19, "LLM-setting: TEMPERATURE-GROQ",            "Temperature",                    "",        "Number",    "",                                                "0.2",                     "0.2"),
    (20, "LLM-setting: ANALYSIS-MODEL-GEMINI",       "Analysis Model",                 "",        "Text",      "",                                                "gemini-2.5-flash",        "gemini-2.5-flash"),
    (21, "LLM-setting: SELENIUM-MODEL-GEMINI",       "Selenium Model",                 "",        "Text",      "",                                                "gemini-2.5-flash",        "gemini-2.5-flash"),
    (22, "LLM-setting: RESULT-ANALYSIS-MODEL-GEMINI","Result Analysis Model",          "",        "Text",      "",                                                "gemini-2.5-flash",        "gemini-2.5-flash"),
    (23, "LLM-setting: TEMPERATURE-GEMINI",          "Temperature",                    "",        "Number",    "",                                                "0.1",                     "0.1"),
    (24, "LLM-setting: ANALYSIS-MODEL-ANTHROPIC",    "Analysis Model",                 "",        "Text",      "",                                                "claude-3-7-sonnet-latest","claude-3-7-sonnet-latest"),
    (25, "LLM-setting: SELENIUM-MODEL-ANTHROPIC",    "Selenium Model",                 "",        "Text",      "",                                                "claude-sonnet-4-20250514","claude-sonnet-4-20250514"),
    (26, "LLM-setting: RESULT-ANALYSIS-MODEL-ANTHROPIC","Result Analysis Model",       "",        "Text",      "",                                                "claude-3-7-sonnet-latest","claude-3-7-sonnet-latest"),
    (27, "LLM-setting: TEMPERATURE-ANTHROPIC",       "Temperature",                    "",        "Number",    "",                                                "0.2",                     "0.2"),
    (28, "LLM-setting: ANALYSIS-MODEL-OLLAMA",       "Analysis Model",                 "",        "Text",      "",                                                "qwen2.5-coder:7b-instruct","qwen2.5-coder:7b-instruct"),
    (29, "LLM-setting: SELENIUM-MODEL-OLLAMA",       "Selenium Model",                 "",        "Text",      "",                                                "qwen2.5-coder:7b-instruct","qwen2.5-coder:7b-instruct"),
    (30, "LLM-setting: RESULT-ANALYSIS-MODEL-OLLAMA","Result Analysis Model",          "",        "Text",      "",                                                "qwen2.5-coder:7b-instruct","qwen2.5-coder:7b-instruct"),
    (31, "LLM-setting: TEMPERATURE-OLLAMA",          "Temperature",                    "",        "Number",    "",                                                "0.2",                     "0.2"),
]

def _normalize_type(t: str) -> str:
    return _TYPE_NORMALIZE.get((t or "").strip(), "Text")

def seed_settings(db: Session):
    """
    Idempotent seeding for Setting rows from Seed-Data-Setting.xlsx.
    Upserts by unique key.
    """
    for (_id, key, title, description, t, possible_values, default_value, actual_value) in _SETTING_SEED_ROWS:
        key = (key or "").strip()
        if not key:
            continue
        norm_type = _normalize_type(t)
        # fetch existing by unique key
        existing = db.execute(select(Setting).where(Setting.key == key)).scalars().one_or_none()
        if existing:
            existing.title = title or None
            existing.description = description or None
            existing.type = norm_type  # enum value text is stored
            existing.possible_values = (possible_values or None)
            existing.default_value = (default_value or None)
            existing.actual_value = (actual_value or None)
        else:
            row = Setting(
                key=key,
                title=title or None,
                description=description or None,
                type=norm_type,
                possible_values=(possible_values or None),
                default_value=(default_value or None),
                actual_value=(actual_value or None),
            )
            db.add(row)
    db.commit()

# from app.models.setting import Setting

_PROMPT_KEY = "Prompt-setting: PROMPT"

# Adjust if you choose a different location
# PROMPT_FILE_PATH = Path(__file__).resolve().parent.parent / "app" / "assets" / "prompts4.yaml"
PROMPT_FILE_PATH = Path(__file__).resolve().parents[1] / "assets" / "prompts4.yaml"

_PROMPTS4_YAML = """\
llm_page_analysis: system: "You are a web page analyst. Extract structural and functional metadata from HTML." user: | Analyze this web page structure and return JSON metadata: {{ "auth_requirements": {{ "auth_required": boolean, "auth_type": "login|registration|none", "auth_fields": [ {{ "name": "field_name", "type": "email|text|password", "required": boolean, "selector": "css_selector_or_xpath", "validation_indicators": [ {{ "type": "class|style|element|attribute|alert", "value": "class_name|style_property|element_selector|attribute_name|alert_message", "description": "e.g., 'red border', 'exclamation mark', 'pattern attribute', 'JS alert for invalid input'" }} ], "default_value": "visible_default_value_if_any" }} ], "credentials_hint": "text_or_element_containing_credentials" }}, "contact_form_fields": [ {{ "id": "form_id", "action": "form_action_url", "method": "get|post", "fields": [ {{ "name": "field_name", "type": "text|email|password|checkbox|radio|select|file", "required": boolean, "selector": "css_selector_or_xpath", "validation_indicators": [ {{ "type": "class|style|element|attribute|alert", "value": "class_name|style_property|element_selector|attribute_name|alert_message", "description": "e.g., 'red border', 'exclamation mark', 'pattern attribute', 'JS alert for invalid input'" }} ] }} ], "submit_button": {{ "text": "button_text", "selector": "css_selector_or_xpath" }} }} ], "interactive_elements": [ {{ "type": "button|link|menu|dropdown|accordion", "text": "element_text_or_image_alt", "selector": "css_selector_or_xpath", "action": "click|hover|submit", "expected_outcome": "e.g., 'redirects to /path', 'opens modal', 'expands menu'", "sub_elements": [ {{ "type": "button|link|menu|dropdown", "text": "sub_element_text_or_image_alt", "selector": "sub_element_selector", "action": "click|hover", "expected_outcome": "e.g., 'redirects to /to_that_page_name', 'expands submenu'" }} ] }} ], "ui_validation_indicators": [ {{ "element_selector": "css_selector_or_xpath", "validation_type": "attribute|masking|state_change", "validation_value": "attribute_name|masked|state_description", "description": "e.g., 'pattern attribute present', 'input is masked', 'checkbox toggles visually'" }} ], "main_content": "Brief description of main content areas", "key_actions": ["list of primary user actions"], "content_hierarchy": {{ "primary_sections": ["section1", "section2"], "subsections": ["subsection1", "subsection2"] }}, "security_indicators": ["https", "captcha", "csrf_token", "otp", "file_upload"] }} Current page HTML: {page_source} Focus on: - All forms and their fields, including types, requirements, and submission details - Forms should be categorized based on their purpose: - **Login/Registration forms**: Place under `auth_requirements` if they involve authentication (e.g., username, password fields) only in the page provided. - Do not consider already logged in user under this category - **Contact forms**: Place under `contact_form_fields` only if they are explicitly for contact purposes (e.g., name, email, message fields). Identify contact forms by: - Field names like 'name', 'email', 'message', 'subject', or similar - Form action URLs containing '/contact', '/support', '/inquiry', or similar/related endpoints - Contextual clues like labels or nearby text (e.g., 'Contact Us', 'Get in Touch') - **Other forms** (e.g., search forms, filters): Place under `interactive_elements` with `type: form`, including a `form_details` object with fields and submit button info. Examples include: - Search forms (e.g., action='/search', fields like 'q' or 'query') - Filter forms (e.g., fields like 'sort', 'category') - For all forms/elements, include only visible, non-hidden input fields (e.g., exclude `type='hidden'` unless they are critical for functionality, like CSRF tokens or security-related fields). Hidden fields should be omitted unless explicitly tied to user-facing actions or security (e.g., `csrf_token`). - Interactive elements like buttons, links, menus, and their actions, including all sub-elements (e.g., menu items) - For links that contain images, set the "text" field to the image's `alt` text, or a descriptive phrase like "Logo image" if no `alt` is present - Include "expected_outcome" for each interactive element, such as "redirects to /path" for links, based on the `href` attribute or other indicators - UI elements indicating validation states (e.g., classes like 'is-invalid', style changes like 'border-color: red', icons like '!', JS alerts, attributes like 'pattern') - Semantic HTML structure - User interaction patterns (e.g., clicking menus to expand or redirect) - Content organization - Security features, including https, captcha, csrf_token, OTP and file upload fields - Specifically look for: - Classes or attributes indicating invalid states (e.g., 'is-invalid', 'error') - CSS changes (e.g., border colors), inline elements (e.g., '!' icons), or JS alerts for validation - Full menu structures, including all sub-items, with expected actions (e.g., redirection URLs) - Page-specific validation behaviors beyond explicit error messages (e.g., masking, pattern enforcement) - Any visible default credentials or hints for login (e.g., text like 'Username: testuser' or 'Password: testpass123') - For accordions: - Only classify elements as "accordion" if they have expandable/collapsible behavior, confirmed by: - JavaScript event listeners (e.g., `click` handlers toggling visibility, inferred from classes like `toggle` or `collapse`) - CSS classes indicating toggling (e.g., `collapse`, `accordion`, `expand`) - HTML structure with headers and collapsible content (e.g., `\
"""

def seed_prompt_setting(db: Session):
    """
    Load prompts4.yaml from disk and upsert the 'Prompt-setting: PROMPT' row
    so that both default_value and actual_value equal the file contents.
    """
    try:
        content = PROMPT_FILE_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        # If file is missing, skip gracefully to avoid startup failure
        print(f"[seed] prompts4.yaml not found at {PROMPT_FILE_PATH}; skipping prompt seed")
        return
    
    row = db.execute(select(Setting).where(Setting.key == _PROMPT_KEY)).scalars().one_or_none()
    if row:
        # row.default_value = _PROMPTS4_YAML
        # row.actual_value = _PROMPTS4_YAML
        row.default_value = content
        row.actual_value = content
    else:
        # If the Setting row doesn’t exist yet, create it with minimal required fields.
        # Type: “Text” per your settings enum; title/description optional.
        row = Setting(
            key=_PROMPT_KEY,
            title="Prompt",
            description=None,
            type="Text",
            possible_values=None,
            default_value=content,
            actual_value=content,
        )
        db.add(row)
    db.commit()
