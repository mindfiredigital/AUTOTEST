import json
import re
from datetime import datetime
from bs4 import BeautifulSoup, Comment
from app.config.database import SessionLocal
from shared_orm.models.page import Page
from app.extractor.navigation_extractor import NavigationExtractor
from shared_orm.models.page_link import PageLink
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException
)

class PageAnalysisService:

    def __init__(self, driver, logger, llm, prompt_manager):
        self.driver = driver
        self.logger = logger
        self.llm = llm
        self.prompt_manager = prompt_manager

    def analyze_page(self, page_id: int, page_url: str, requested_by: str):
        
        self.logger.info(f"[PAGE_ANALYSE] Loading {page_url}")

        self.logger.info(f"[PAGE_ANALYSE] Current URL before analysis: {self.driver.current_url}")

        self.logger.debug(f"[PAGE_ANALYSE] Updating Page ID: {page_id}")
        if self.driver.current_url != page_url:
            self.driver.get(page_url)

        WebDriverWait(self.driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body")))

        page_source = self.driver.page_source
        self.logger.debug(f"[PAGE_ANALYSE] Page title: {self.driver.title}")
        self.logger.debug(f"[PAGE_ANALYSE] Page HTML length: {len(page_source)}")
        minimized_html = self.extract_test_relevant_html(page_source) # fetch page source

        static_metadata = {
            "title": self.driver.title,
            "url": self.driver.current_url,
            "forms": self.extract_forms(),
            "buttons": self.extract_interactive_elements(),
            "tables": self.extract_data_tables(),
            "key_flows": self.identify_key_flows()

        }

        llm_metadata = self.llm_page_analysis(minimized_html) # fetch page metadata

        page_metadata = {
            **static_metadata,
            **llm_metadata
        }
        with SessionLocal() as db:
            page = db.query(Page).filter(Page.id == page_id).first()
            if not page:
                self.logger.error(f"[PAGE_ANALYSE] Page record not found for id={page_id}")
                return

            page.page_title = self.driver.title
            page.page_source = minimized_html
            page.page_metadata = page_metadata
            page.status = "generating_test_scenarios"
            page.updated_on = datetime.utcnow()
            page.updated_by = requested_by
            db.flush()
            db.commit()
            self.logger.info(f"[PAGE_ANALYSE] Page metadata stored | page_id={page_id}")
            self._save_page_links(
                db=db,
                source_page=page,
                html=page_source,
                requested_by=requested_by
            )
            
    def _save_page_links(self, db, source_page: Page, html: str, requested_by: int):
        extractor = NavigationExtractor(source_page.page_url)
        events = extractor.extract(html)
        DEFAULT_TEST_SCENARIO_ID = 0


        for event in events:
            target_page = db.query(Page).filter(
                Page.page_url == event["target_url"]
            ).first()

            if not target_page:
                target_page = Page(
                    site_id=source_page.site_id,
                    page_url=event["target_url"],
                    status="new",
                    created_on=datetime.utcnow(),
                    created_by=requested_by
                )
                db.add(target_page)
                db.flush()

            exists = db.query(PageLink).filter(
                PageLink.page_id_source == source_page.id,
                PageLink.page_id_target == target_page.id,
                PageLink.event_selector == event["selector"]
            ).first()

            if exists:
                continue

            link = PageLink(
                page_id_source=source_page.id,
                page_id_target=target_page.id,
                test_scenario_id_source=DEFAULT_TEST_SCENARIO_ID,
                event_selector=event["selector"],
                event_description=event["description"]
            )

            db.add(link)

        db.flush()
        db.commit()

    def extract_test_relevant_html(self, page_source):
        soup = BeautifulSoup(page_source, "html.parser")


        # Remove scripts, styles, meta, and comments
        for tag in soup(["script", "meta", "link", "style", "path", "noscript"]):
            tag.decompose()

        # for tag in soup(tags_to_remove):
        #     tag.decompose()

        # Optionally, remove comments and whitespace
        for element in soup(text=lambda text: isinstance(text, Comment)):
            element.extract()
        # # Extract only forms, buttons, inputs, links, tables, selects, textareas
        # relevant = []
        # for tag in ["form", "input", "button", "a", "select", "table", "textarea"]:
        #     relevant.extend(soup.find_all(tag))
        # Convert back to string, limit to N elements per type if needed
        # relevant_html = "\n".join(str(el) for el in relevant[:20])  # cap at 20 elements/type
        # return relevant_html

        # Get the HTML string
        html_string = str(soup)

        # Remove excessive whitespace and blank lines
        # Replace multiple consecutive whitespace characters with single space
        html_string = re.sub(r'\s+', ' ', html_string)
        
        # Remove leading/trailing whitespace from each line and remove empty lines
        lines = html_string.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line:  # Only keep non-empty lines
                cleaned_lines.append(stripped_line)
        
        # Join lines with single newlines
        cleaned_html = '\n'.join(cleaned_lines)
        
        # Alternative approach: More aggressive whitespace cleanup
        # This removes all unnecessary whitespace between tags while preserving content
        cleaned_html = re.sub(r'>\s+<', '><', cleaned_html)
        
        return cleaned_html
      
    def llm_page_analysis(self, minimized_html):
        """
        Perform dynamic page analysis using LLM
        
        Args:
            page_source (str): HTML source of the page
            
        Returns:
            dict: LLM analysis results
        """
        try:
            system_prompt = self.prompt_manager.get_prompt("llm_page_analysis", "system")
            # self.logger.debug(f"LLM analysis system prompt: {system_prompt}")
            # test_data = self.load_test_data()
            # self.logger.debug(f"Test Data: {test_data}")
            self.logger.debug("Sending request to LLM for page metadata extraction...")
            
            user_prompt_template = self.prompt_manager.get_prompt("llm_page_analysis", "user")
            user_prompt = user_prompt_template.format(page_source=minimized_html)
            # self.logger.debug(f"LLM analysis user prompt: {user_prompt}")
            
            result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")
            
            self.logger.debug("LLM extraction of current page metadata completed")
            # self.logger.debug(f"Raw LLM response: {result}")
            
            try:
                # Parse JSON response
                json_str = result
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].strip()

                # self.logger.debug(f"Sanitized LLM response: {json_str}")
                return json.loads(json_str)
            
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response: {str(e)}")
                return {}
            
        except Exception as e:
            self.logger.error(f"LLM page analysis failed: {str(e)}")
            return {}
   
    def extract_forms(self):
        """Extract form information from current page"""
        forms = []
        for form in self.driver.find_elements(By.TAG_NAME, 'form'):
            form_data = {
                "id": form.get_attribute('id'),
                "action": form.get_attribute('action'),
                "method": form.get_attribute('method'),
                "inputs": [],
                "buttons": []
            }
            
            for inp in form.find_elements(By.TAG_NAME, 'input'):
                form_data["inputs"].append({
                    "type": inp.get_attribute('type'),
                    "name": inp.get_attribute('name'),
                    "id": inp.get_attribute('id')
                })
                
            for btn in form.find_elements(By.TAG_NAME, 'button'):
                form_data["buttons"].append({
                    "type": btn.get_attribute('type'),
                    "text": btn.text,
                    "id": btn.get_attribute('id')
                })
                
            forms.append(form_data)
        return forms
    
    def extract_interactive_elements(self):
        """Extract interactive elements from current page"""
        return [{
            "tag": el.tag_name,
            "text": el.text[:50],
            "id": el.get_attribute('id'),
            "type": el.get_attribute('type')
        } for el in self.driver.find_elements(By.CSS_SELECTOR, 
                                            'button, a, input, select, textarea')]
   
    def extract_data_tables(self):
        """Extract table information from current page"""
        return [{
            "id": table.get_attribute('id'),
            "headers": [th.text for th in table.find_elements(By.TAG_NAME, 'th')],
            "row_count": len(table.find_elements(By.TAG_NAME, 'tr'))
        } for table in self.driver.find_elements(By.TAG_NAME, 'table')]
    
    def identify_key_flows(self):
        """Identify key user flows on current page"""
        return {
            "main_navigation": [a.get_attribute('href') for a in
                              self.driver.find_elements(By.CSS_SELECTOR, 'nav a, .menu a')[:5]],
            "primary_actions": [btn.text for btn in
                              self.driver.find_elements(By.CSS_SELECTOR, '.primary-btn, .cta-button')]
        }

    # -----------------------------------------------------------------------
    # AUTHENTICATION HANDLER
    # This method attempts to log in to the website using provided credentials.
    # It uses LLM to identify the login form fields and submit button.
    # Returns True if login is successful, False otherwise.
    # -----------------------------------------------------------------------
    # def login_to_website(self, url, username=None, password=None):
    #     if not username or not password:
    #         raise ValueError("Credentials required")

    #     try:
    #         self.logger.info("Starting authentication")

    #         self.driver.get(url)

    #         WebDriverWait(self.driver, 10).until(
    #             EC.presence_of_element_located((By.TAG_NAME, "body"))
    #         )

    #         page_html = self.driver.page_source

    #         system_prompt = self.prompt_manager.get_prompt("auth_form_selectors", "system")
    #         user_prompt = self.prompt_manager.get_prompt("auth_form_selectors", "user").format(
    #             page_html=page_html
    #         )

    #         result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")

    #         json_str = result
    #         if "```json" in result:
    #             json_str = result.split("```json")[1].split("```")[0].strip()
    #         elif "```" in result:
    #             json_str = result.split("```")[1].strip()

    #         auth_data = json.loads(json_str)

    #         username_selector = auth_data.get("username_selector")
    #         password_selector = auth_data.get("password_selector")
    #         submit_selector   = auth_data.get("submit_selector")

    #         if not username_selector or not password_selector or not submit_selector:
    #             raise RuntimeError("Invalid auth selector structure")

    #         # Fill username
    #         user_field = self.driver.find_element(By.CSS_SELECTOR, username_selector)
    #         user_field.clear()
    #         user_field.send_keys(username)

    #         # Fill password
    #         pass_field = self.driver.find_element(By.CSS_SELECTOR, password_selector)
    #         pass_field.clear()
    #         pass_field.send_keys(password)

    #         # Submit
    #         submit_button = self.driver.find_element(By.CSS_SELECTOR, submit_selector)
    #         self.driver.execute_script("arguments[0].click();", submit_button)

    #         # Wait for redirect or load
    #         WebDriverWait(self.driver, 10).until(
    #             lambda d: d.execute_script("return document.readyState") == "complete"
    #         )

    #         # Validate login success
    #         if self.driver.current_url == url:
    #             self.logger.warning("Login did not redirect.")
    #             return False

    #         if "logout" in self.driver.page_source.lower():
    #             self.logger.info("Logout detected — login success.")
    #             return True

    #         return True

    #     except Exception as e:
    #         self.logger.error(f"Authentication failed: {str(e)}")
    #         return False

        
    def login_to_website(self, username: str, password: str) -> bool:
        """
        Perform dynamic login using LLM-discovered selectors.
        Designed for async worker flow (no interactive input).
        """

        if not username or not password:
            raise ValueError("Credentials required for authentication")

        try:
            
            self.logger.debug("[AUTH] Authentication started")

            wait = WebDriverWait(self.driver, 15)

            # Ensure page is loaded
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            page_html = self.driver.page_source

            # ---- Ask LLM for form selectors ----
            system_prompt = self.prompt_manager.get_prompt(
                "auth_form_selectors", "system"
            )
            user_prompt = self.prompt_manager.get_prompt(
                "auth_form_selectors", "user"
            ).format(page_html=page_html)

            result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")

            try:
                json_str = result.strip()

                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].strip()

                auth_data = json.loads(json_str)

            except Exception as e:
                self.logger.error(f"[AUTH] Failed parsing selector JSON: {e}")
                return False

            self.logger.debug(f"[AUTH] Selectors resolved: {auth_data}")

            # ---- Wait for form fields ----
            username_selector = auth_data.get("username_selector")
            password_selector = auth_data.get("password_selector")
            submit_selector = auth_data.get("submit_selector")

            if not username_selector or not password_selector or not submit_selector:
                self.logger.error(f"[AUTH] Missing required selectors from LLM, Username selector: {username_selector}, Password selector: {password_selector}, Submit selector: {submit_selector}")
                return False
            self.logger.debug(f"[AUTH] Username selector: {username_selector}")
            self.logger.debug(f"[AUTH] Password selector: {password_selector}")
            self.logger.debug(f"[AUTH] Submit selector: {submit_selector}")

            

            username_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, username_selector))
            )
            password_field = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, password_selector))
            )

            # Clear existing values (important for re-runs)
            username_field.clear()
            password_field.clear()

            username_field.send_keys(username)
            password_field.send_keys(password)

            # ---- Click submit ----
            submit_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, submit_selector))
            )
            current_url = self.driver.current_url

            try:
                submit_button.click()
                
            except ElementClickInterceptedException:
                self.logger.debug("[AUTH] Click intercepted, using JS click")
                self.driver.execute_script("arguments[0].click();", submit_button)
            
            try:
                wait.until(EC.url_changes(current_url))
                self.logger.debug("[AUTH] URL changed after login")
            except TimeoutException:
                self.logger.debug("[AUTH] URL did not change after login")

            self.logger.debug(f"[AUTH] URL after login: {self.driver.current_url}")
            

            # ---- Wait for redirect or DOM change ----
            # wait.until(lambda d: d.current_url != self.driver.current_url)

            # Small additional stabilization wait
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            page_html_after = self.driver.page_source

            # ---- First try deterministic check ----
            if "logout" in page_html_after.lower():
                self.logger.info("[AUTH] Login detected via logout presence")
                return True

            # ---- Fallback to LLM login state check ----
            is_logged = self.llm_is_logged_in(page_html_after)

            if not is_logged:
                self.logger.warning("[AUTH] LLM indicates login failed")
                return False

            self.logger.info("[AUTH] Login successful")
            return True

        except TimeoutException:
            self.logger.error("[AUTH] Timeout during authentication")
            return False

        except NoSuchElementException as e:
            self.logger.error(f"[AUTH] Element not found: {e}")
            return False

        except Exception as e:
            self.logger.error(f"[AUTH] Unexpected authentication error: {e}")
            return False
        
    def llm_is_logged_in(self, page_html):
       system_prompt = self.prompt_manager.get_prompt("login_state_check", "system")
       user_prompt_template = self.prompt_manager.get_prompt("login_state_check", "user")
       user_prompt = user_prompt_template.format(page_html=page_html)
       result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")
       try:
          data = json.loads(result)
          logged_in = data.get("logged_in", False)
          self.logger.info(f"Authentication state returned by llm: {logged_in}")
          return logged_in
       except Exception as e:
         self.logger.error(f"[AUTH] Failed parsing login state JSON: {e}")
         return False   


    