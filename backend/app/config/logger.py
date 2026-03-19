import logging
import re
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime

LOG_DIR = "logs"

current_date = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = f"autotest_{current_date}.log"

os.makedirs(LOG_DIR, exist_ok=True)

# Patterns to redact: key=value or "key": "value" forms
_SENSITIVE_KEYS = re.compile(
    r'(?i)(password|passwd|secret|api[_-]?key|token|authorization|auth|key)\s*'
    r'[:=]\s*["\']?([^"\',\s\]}{]+)["\']?'
)
_REPLACEMENT = r'\1=***REDACTED***'


class SensitiveDataFilter(logging.Filter):
    """Redacts passwords, tokens, and API keys from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _SENSITIVE_KEYS.sub(_REPLACEMENT, record.msg)
        if record.args:
            try:
                if isinstance(record.args, dict):
                    record.args = {
                        k: "***REDACTED***" if isinstance(v, str) and _SENSITIVE_KEYS.search(f"{k}={v}") else v
                        for k, v in record.args.items()
                    }
                elif isinstance(record.args, tuple):
                    record.args = tuple(
                        _SENSITIVE_KEYS.sub(_REPLACEMENT, a) if isinstance(a, str) else a
                        for a in record.args
                    )
            except Exception:
                pass
        return True


def setup_logger():
    logger = logging.getLogger("autotest")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Prevent duplicate handlers (important in FastAPI reload mode)
    if logger.handlers:
        logger.handlers.clear()

    logger.addFilter(SensitiveDataFilter())

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # ----------------------------
    # File Handler (Rotating)
    # ----------------------------
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, LOG_FILE),
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
        utc=False
    )
    file_handler.setFormatter(formatter)

    # ----------------------------
    # Console Handler
    # ----------------------------
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Add Handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()