import pytest
from autotest import WebTestGenerator

def test_web_test_generator_init():
    tester = WebTestGenerator()
    assert tester is not None
    assert tester.log_level == "INFO"

def test_supported_languages():
    from autotest.core.web_test_generator import SUPPORTED_LANGUAGES
    assert "selenium" in SUPPORTED_LANGUAGES
    assert "python" in SUPPORTED_LANGUAGES["selenium"]