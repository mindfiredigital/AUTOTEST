"""
Logging utilities for the autotest package
"""
import logging
import os
from datetime import datetime


class ContextFilter(logging.Filter):
    """Custom logging filter to add context information"""
    
    def filter(self, record):
        """Add test_cases attribute if not present"""
        if not hasattr(record, 'test_cases'):
            record.test_cases = []
        return True


def setup_logger(name, log_level="INFO", log_to_file=True, log_dir="logs"):
    """
    Set up a logger with console and optional file handlers
    
    Args:
        name (str): Logger name
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file (bool): Whether to log to file
        log_dir (str): Directory for log files
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Convert string log level to numeric value
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # Remove existing handlers to prevent duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if requested
    if log_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"test_run_{timestamp}.log")
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add custom filter
    logger.addFilter(ContextFilter())
    logger.propagate = False  # Prevent duplicate logs
    
    return logger


def get_package_logger(log_level="INFO"):
    """
    Get a pre-configured logger for the autotest package
    
    Args:
        log_level (str): Logging level
        
    Returns:
        logging.Logger: Configured logger
    """
    return setup_logger("AutoTestPackage", log_level)


class LoggerMixin:
    """Mixin class to add logging capabilities to other classes"""
    
    def __init__(self, logger_name=None, log_level="INFO"):
        """
        Initialize logger mixin
        
        Args:
            logger_name (str): Name for the logger
            log_level (str): Logging level
        """
        if logger_name is None:
            logger_name = self.__class__.__name__
        self.logger = setup_logger(logger_name, log_level)
    
    def log_info(self, message):
        """Log info message"""
        self.logger.info(message)
    
    def log_debug(self, message):
        """Log debug message"""
        self.logger.debug(message)
    
    def log_warning(self, message):
        """Log warning message"""
        self.logger.warning(message)
    
    def log_error(self, message):
        """Log error message"""
        self.logger.error(message)
    
    def log_critical(self, message):
        """Log critical message"""
        self.logger.critical(message)