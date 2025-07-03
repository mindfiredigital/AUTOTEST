"""
AutoTest Package - Automated Web Testing Framework
"""

from .core.web_test_generator import WebTestGenerator
from .core.llm_wrapper import LLMWrapper
from .core.prompt_manager import PromptManager
from .core.url_extractor import URLExtractor
from .utils.logging_utils import ContextFilter

__version__ = "1.0.0"
__author__ = "Ankit Saha"
__email__ = "ankit.s@mindfiresolutions.com"

__all__ = [
    'WebTestGenerator',
    'LLMWrapper', 
    'PromptManager',
    'URLExtractor',
    'ContextFilter'
]