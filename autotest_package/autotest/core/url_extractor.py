"""
URL Extractor module for recursive URL discovery
"""
import time
import logging
from urllib.parse import urlparse, urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class URLExtractor:
    """Class for extracting URLs from web pages recursively"""
    
    def __init__(self, driver, logger=None):
        """
        Initialize URL extractor
        
        Args:
            driver: Selenium WebDriver instance
            logger: Logger instance (optional)
        """
        self.driver = driver
        self.logger = logger or logging.getLogger(__name__)
        
    def extract_urls(self, base_url, max_depth=2):
        """
        Recursively extract unique internal URLs with BFS up to max_depth
        
        Args:
            base_url (str): Base URL to start extraction from
            max_depth (int): Maximum depth for recursive extraction
            
        Returns:
            list: Sorted list of unique URLs found
        """
        self.logger.info(f"Starting recursive URL extraction from: {base_url}")
        
        try:
            parsed_base = urlparse(base_url)
            base_domain = parsed_base.netloc
            visited = set()
            to_visit = [(base_url, 0)]  # (url, depth)

            while to_visit:
                current_url, depth = to_visit.pop(0)
                
                if current_url in visited or depth > max_depth:
                    continue
                
                try:
                    self.logger.debug(f"Waiting 1 sec. before processing {current_url}")
                    time.sleep(1)
                    self.driver.get(current_url)
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, 'body'))
                    )
                    visited.add(current_url)
                    self.logger.info(f"Processing depth {depth}: {current_url}")

                    # Extract links from current page
                    links = self.driver.find_elements(By.TAG_NAME, 'a')
                    new_urls = set()

                    for link in links:
                        href = link.get_attribute('href')
                        if not href:
                            continue
                            
                        full_url = urljoin(current_url, href)
                        parsed_url = urlparse(full_url)
                        
                        if parsed_url.netloc == base_domain:
                            # Normalize path and handle root URL
                            path = parsed_url.path.rstrip('/') or '/'
                            clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{path}"
                            if clean_url not in visited:
                                new_urls.add(clean_url)

                    # Add discovered URLs to queue
                    for url in new_urls:
                        if url not in [u for u, _ in to_visit]:
                            to_visit.append((url, depth + 1))
                            
                    self.logger.debug(f"Found {len(new_urls)} new URLs at depth {depth}")

                except Exception as e:
                    self.logger.error(f"Failed to process {current_url}: {str(e)}")

            self.logger.info(f"Total unique URLs found: {len(visited)}")

            for url in visited:
                self.logger.debug(f"Found URL: {url}")

            return sorted(visited)
            
        except Exception as e:
            self.logger.error(f"URL extraction failed: {str(e)}")
            return []
    
    def extract_links_from_page(self, url):
        """
        Extract all links from a single page
        
        Args:
            url (str): URL to extract links from
            
        Returns:
            list: List of href attributes found on the page
        """
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            links = self.driver.find_elements(By.TAG_NAME, 'a')
            hrefs = []
            
            for link in links:
                href = link.get_attribute('href')
                if href:
                    hrefs.append(href)
                    
            self.logger.debug(f"Found {len(hrefs)} links on {url}")
            return hrefs
            
        except Exception as e:
            self.logger.error(f"Failed to extract links from {url}: {str(e)}")
            return []
    
    def is_internal_url(self, url, base_domain):
        """
        Check if URL belongs to the same domain
        
        Args:
            url (str): URL to check
            base_domain (str): Base domain to compare against
            
        Returns:
            bool: True if URL is internal, False otherwise
        """
        try:
            parsed_url = urlparse(url)
            return parsed_url.netloc == base_domain
        except Exception:
            return False
    
    def normalize_url(self, url):
        """
        Normalize URL by removing fragments and normalizing path
        
        Args:
            url (str): URL to normalize
            
        Returns:
            str: Normalized URL
        """
        try:
            parsed = urlparse(url)
            path = parsed.path.rstrip('/') or '/'
            return f"{parsed.scheme}://{parsed.netloc}{path}"
        except Exception:
            return url