from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def get_driver():
    """
    Initialize and return a headless Chromium WebDriver.

    Configured for use in server or container environments with
    required flags for stability and performance.
    """

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.binary_location = "/usr/bin/chromium"

    # Run in headless mode with necessary flags
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Incognito ensures each driver starts with a clean session — no cookies or
    # cached state from previous runs bleed across subprocess invocations.
    chrome_options.add_argument("--incognito")

    # Set up ChromeDriver service
    service = Service("/usr/bin/chromedriver")

    # Create and return WebDriver instance
    return webdriver.Chrome(service=service, options=chrome_options)