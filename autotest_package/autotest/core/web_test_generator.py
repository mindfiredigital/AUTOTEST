"""
Main Web Test Generator module
"""

import os
import json
import re
import subprocess
import tempfile
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException,
                                      NoSuchElementException,
                                      StaleElementReferenceException)
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime
from jsonschema import validate, ValidationError

from .llm_wrapper import LLMWrapper
from .prompt_manager import PromptManager
from .url_extractor import URLExtractor
from ..utils.logging_utils import setup_logger

# Load environment variables
load_dotenv()

# Constants
SUPPORTED_LANGUAGES = {
    "selenium": ["python", "java", "csharp", "javascript", "ruby"],
    "playwright": ["python", "javascript", "csharp", "java"],
    "puppeteer": ["python"]
}

AUTH_DATA_SCHEMA = {
    "type": "object",
    "properties": {
        "credentials": {
            "type": "object",
            "properties": {
                "valid": {"type": "object"},
                "invalid": {"type": "object"}
            }
        },
        "registration_fields": {
            "type": "object",
            "patternProperties": {
                "^.*$": {
                    "type": "object",
                    "properties": {
                        "valid": {"type": "array"},
                        "invalid": {"type": "array"}
                    }
                }
            }
        },
        "contact_form": {
            "type": "object",
            "properties": {
                "valid": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "message": {"type": "string"}
                    }
                },
                "invalid": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"},
                        "message": {"type": "string"}
                    }
                }
            }
        }
    }
}

class WebTestGenerator:
    """Main class for automated web test generation"""
    
    def __init__(self, log_level="INFO", selenium_version="4.15.2", 
                 wait_time="", testing_tool="selenium", language="python"):
        """
        Initialize WebTestGenerator
        
        Args:
            log_level (str): Logging level
            selenium_version (str): Selenium version for generated scripts
            wait_time (str): Custom wait time for CAPTCHA handling
            testing_tool (str): Testing framework to use
            language (str): Programming language for test scripts
        """
        self.log_level = log_level.upper()
        self.selenium_version = selenium_version
        self.wait_time = wait_time
        self.testing_tool = testing_tool.lower()
        
        # Validate language support
        valid_langs = SUPPORTED_LANGUAGES.get(testing_tool.lower(), [])
        if language.lower() not in valid_langs:
            raise ValueError(
                f"'{language}' not supported for {testing_tool}. "
                f"Valid options: {', '.join(valid_langs)}"
            )
        
        self.language = language.lower()
        
        # Initialize components
        self.llm = LLMWrapper()
        self.prompt_manager = PromptManager()
        self.driver = None
        self.visited_pages = set()
        self.test_results = []
        self.logger = setup_logger("WebTestGenerator", log_level)
        self.temperature = 0.3
        
        # Setup browser and URL extractor
        self.setup_browser()
        self.url_extractor = URLExtractor(self.driver, self.logger)

    def setup_browser(self):
        """Setup Chrome browser with headless configuration"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        service = Service()
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def capture_screenshot(self):
        """Capture and return base64 encoded screenshot"""
        screenshot = self.driver.get_screenshot_as_png()
        img = Image.open(BytesIO(screenshot))
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    def analyze_page(self, context="current"):
        """
        Analyze current page and generate metadata
        
        Args:
            context (str): Context description for logging
            
        Returns:
            dict: Page analysis results with metadata, test cases, and scripts
        """
        self.logger.info(f"Analyzing {context} page...")
        page_source = self.driver.page_source
        #self.logger.info(f"PAGE_SOURCE: {page_source}")
        
        # Static metadata extraction
        static_metadata = {
            "title": self.driver.title,
            "url": self.driver.current_url,
            "forms": self.extract_forms(),
            "buttons": self.extract_interactive_elements(),
            "tables": self.extract_data_tables(),
            "key_flows": self.identify_key_flows()
        }
        
        self.logger.debug(f"Static page metadata: {static_metadata}")
        
        # LLM-powered dynamic analysis
        llm_metadata = self.llm_page_analysis(page_source)
        self.logger.debug(f"LLM Analysed page metadata: {llm_metadata}")
        
        # Combine static and dynamic metadata
        page_metadata = {**static_metadata, **llm_metadata}
        self.logger.debug(f"Combined page metadata: {page_metadata}")
        
        # Generate test cases and scripts
        test_cases = self.generate_page_specific_tests(page_metadata, page_source)
        scripts = [self.generate_script_for_test_case(tc, page_metadata, page_source) 
                  for tc in test_cases]
        
        return {
            "metadata": page_metadata,
            "test_cases": test_cases,
            "scripts": scripts
        }

    def llm_page_analysis(self, page_source):
        """
        Perform dynamic page analysis using LLM
        
        Args:
            page_source (str): HTML source of the page
            
        Returns:
            dict: LLM analysis results
        """
        try:
            system_prompt = self.prompt_manager.get_prompt("llm_page_analysis", "system")
            self.logger.debug(f"LLM analysis system prompt: {system_prompt}")
            test_data = self.load_test_data()
            self.logger.debug(f"Test Data: {test_data}")
            user_prompt_template = self.prompt_manager.get_prompt("llm_page_analysis", "user")
            user_prompt = user_prompt_template.format(page_source=page_source)
            #self.logger.debug(f"LLM analysis user prompt: {user_prompt}")
            
            result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")
            
            self.logger.info("LLM analysis of current page completed")
            self.logger.debug(f"Raw LLM response: {result}")
            
            try:
                # Parse JSON response
                json_str = result
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].strip()

                self.logger.debug(f"Sanitized LLM response: {json_str}")
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

    def load_test_data(self, file_path=None):
        """
        Load test data from JSON file
        
        Args:
            file_path (str): Path to test data file
            
        Returns:
            dict: Test data or None if loading fails
        """
        if file_path is None:
            # Default to config directory
            package_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            file_path = os.path.join(package_dir, 'config', 'auth_test_data.json')
            
        try:
            with open(file_path) as f:
                data = json.load(f)
            return data
        except Exception as e:
            self.logger.error(f"Failed to load test data: {str(e)}")
            return None

    def generate_page_specific_tests(self, page_metadata, page_source):
        """
        Generate context-aware test cases based on page content
        
        Args:
            page_metadata (dict): Page metadata
            page_source (str): HTML source of the page
            
        Returns:
            list: Generated test cases
        """
        test_data = None
        prompt_suffix_new = ""
        
        # Get prompt suffix templates from YAML
        suffix_templates = self.prompt_manager.get_prompt("generate_tests", "prompt_suffix")
        
        # Handle auth/contact form test data
        if (page_metadata.get('auth_requirements', {}).get('auth_required') or 
            page_metadata.get('contact_form_fields')):
            test_data = self.load_test_data()
            if test_data:
                test_data_suffix = suffix_templates["test_data"].format(
                    test_data=json.dumps(test_data, indent=2),
                    auth_requirements=json.dumps(page_metadata.get('auth_requirements', {}), indent=2)
                )
                prompt_suffix_new += test_data_suffix
        
        # Add contact form fields
        if page_metadata.get('contact_form_fields'):
            contact_form_suffix = suffix_templates["contact_form"].format(
                contact_form_fields=json.dumps(page_metadata['contact_form_fields'][0]['fields'], indent=2)
            )
            prompt_suffix_new += contact_form_suffix
        
        try:
            self.logger.info("Sending request to LLM for test case generation...")
            system_prompt = self.prompt_manager.get_prompt("generate_tests", "system")
            user_prompt_template = self.prompt_manager.get_prompt("generate_tests", "user")
            
            user_prompt = user_prompt_template.format(
                page_metadata=json.dumps(page_metadata, indent=2),
                prompt_suffix=prompt_suffix_new,
                title=page_metadata['title'],
                forms=json.dumps(page_metadata['forms']),
                buttons=json.dumps(page_metadata['buttons']),
                interactive_elements=json.dumps(page_metadata.get('interactive_elements', [])),
                #interactive_elements = json.dumps(page_metadata['interactive_elements']),
                ui_validation_indicators=json.dumps(page_metadata.get('ui_validation_indicators', [])),
                url=page_metadata['url'],
                page_source=page_source
            )
            
            result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")
            self.logger.debug(f"Raw LLM response: {result}")
            self.logger.info("Received response from LLM")
            
            try:
                # Parse JSON response
                json_str = result
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].strip()
                    
                parsed = json.loads(json_str)
                test_cases = parsed['test_cases']
                
                self.logger.info(f"Successfully parsed {len(test_cases)} test cases")
                self.logger.debug("Test Case Details:\n" + json.dumps(test_cases, indent=2))
                
                # Validate test data usage
                if test_data:
                    self._validate_auth_test_data_usage(parsed.get('test_cases', []), test_data)
                    
                return test_cases
            
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON for test cases: {str(e)}")
                self.logger.debug(f"Raw response: {result}")
                return {"test_cases": []}
        except Exception as e:
            self.logger.error(f"Test generation failed: {str(e)}")
            return []
        
    def generate_script_for_test_case(self, test_case, page_metadata, page_source):
        """
        Generate test script for a specific test case
        
        Args:
            test_case (dict): Test case specification
            page_metadata (dict): Page metadata
            page_source (str): HTML source of the page
            
        Returns:
            str: Generated test script code
        """
        captcha_wait_time = self.wait_time or "2 minutes (120 seconds)"
        
        try:
            system_prompt_template = self.prompt_manager.get_prompt(
                "generate_script", "system", tool=self.testing_tool)
            system_prompt = system_prompt_template.format(
                selenium_version=self.selenium_version, 
                language=self.language
            )
            #self.logger.debug(f"system prompt for script generation: {system_prompt}")
            user_prompt_template = self.prompt_manager.get_prompt(
                "generate_script", "user", tool=self.testing_tool)
            user_prompt = user_prompt_template.format(
                language=self.language,
                selenium_version=self.selenium_version,
                test_case=json.dumps(test_case, indent=2),
                page_metadata=json.dumps(page_metadata, indent=2),
                page_source=page_source,
                captcha_wait_time=captcha_wait_time,
                security_indicators=page_metadata.get('security_indicators', [])
            )
            
            script_content = self.llm.generate(system_prompt, user_prompt, model_type="selenium")
            self.logger.debug(f"Raw LLM response generated code: {script_content}")
            
            # Extract code from markdown blocks
            #code = self._extract_code_from_response(script_content)

            if "```python" in script_content:
                code = script_content.split("```python")[1].split("```")[0].strip()
            elif "```java" in script_content:
                code = script_content.split("```java")[1].split("```")[0].strip()
            elif "```" in script_content:
                code = script_content.split("```")[1].strip()
            else:
                code = script_content.strip()
            
            # Save script to file
            # if code:
            #     self._save_script_to_file(code, test_case, script_content)

            if code:  
                script_dir = "test_scripts"
                if not os.path.exists(script_dir):
                    os.makedirs(script_dir)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                # Sanitize the test case name
                # Replace any character that's not alphanumeric, hyphen, or underscore with underscore
                sanitized_name = re.sub(r'[^a-zA-Z0-9\-_]', '_', test_case['name'])
                # Optional: Remove multiple consecutive underscores
                sanitized_name = re.sub(r'_+', '_', sanitized_name)
                # Optional: Remove leading/trailing underscores
                sanitized_name = sanitized_name.strip('_')

                if "```python" in script_content:
                    script_name = f"{script_dir}/test_{timestamp}_{sanitized_name}.py"
                else:
                    script_name = f"{script_dir}/test_{timestamp}_{sanitized_name}.java"

                with open(script_name, 'w') as f:
                    f.write(code)
                    
                self.logger.info(f"Saved test script: {script_name}")
                
            return code
            
        except Exception as e:
            self.logger.error(f"Script generation failed: {str(e)}")
            return ""

    def _extract_code_from_response(self, script_content):
        """Extract code from LLM response, handling markdown blocks"""
        if "```python" in script_content:
            return script_content.split("```python")[1].split("```")[0].strip()
        elif "```java" in script_content:
            return script_content.split("```java")[1].split("```")[0].strip()
        elif "```" in script_content:
            return script_content.split("```")[1].strip()
        else:
            return script_content.strip()

    def _save_script_to_file(self, code, test_case, script_content):
        """Save generated script to file"""
        script_dir = "test_scripts"
        if not os.path.exists(script_dir):
            os.makedirs(script_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_name = re.sub(r'[^a-zA-Z0-9\-_]', '_', test_case['name'])
        sanitized_name = re.sub(r'_+', '_', sanitized_name).strip('_')
        
        if "```python" in script_content:
            extension = ".py"
        else:
            extension = ".java"
        script_name = f"{script_dir}/test_{timestamp}_{sanitized_name}{extension}"
        
        with open(script_name, 'w') as f:
            f.write(code)
        self.logger.info(f"Saved test script: {script_name}")

    def execute_test_cycle(self, analysis):
        """Execute test cycle for page analysis results"""
        for script in analysis['scripts']:
            if not self.validate_script_structure(script):
                continue
            result = self.execute_test_script(script)
            self._log_test_result(result)

    def validate_script_structure(self, script):
        """Validate basic script structure"""
        required_imports = ['from selenium import webdriver', 'By']
        return all(imp in script for imp in required_imports)

    def execute_test_script(self, script):
        """Execute a test script and return results"""
        try:
            if not script.strip():
                return {'success': False, 'error': 'Empty test script'}
                
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
                f.write(script)
                temp_file = f.name
                
            result = subprocess.run(
                ['python', temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Test execution timed out'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            if 'temp_file' in locals() and os.path.exists(temp_file):
                os.remove(temp_file)

    # def run_workflow(self, url, username=None, password=None):
    #     """
    #     Main workflow execution
        
    #     Args:
    #         url (str): URL to test
    #         username (str): Optional username for authentication
    #         password (str): Optional password for authentication
            
    #     Returns:
    #         str: Path to generated report file
    #     """
    #     try:
    #         self.driver.get(url)
    #         initial_analysis = self.analyze_page(context=url)
    #         self.execute_test_cycle(initial_analysis)
    #         self.track_navigation(url)
    #         return self.generate_report()
    #     finally:
    #         if self.driver:
    #             self.driver.quit()

    def run_workflow(self, url, username=None, password=None, recursive=False, max_depth=1):
        """
        Main workflow execution with optional recursive URL discovery
        
        Args:
            url (str): URL to test
            username (str): Optional username for authentication
            password (str): Optional password for authentication
            recursive (bool): Whether to perform recursive URL extraction
            max_depth (int): Maximum depth for recursive extraction
            
        Returns:
            str: Path to generated report file
        """
        try:
            if recursive:
                # Enhanced workflow with recursive URL discovery
                all_urls = self.url_extractor.extract_urls(url, max_depth=max_depth)
                if not all_urls:
                    self.logger.warning("No URLs found to test")
                    return self.generate_report()

                # Process each URL
                for discovered_url in all_urls:
                    self.process_single_url(discovered_url, username, password)
                    
                return self.generate_report()
            else:
                # Original single-page workflow
                self.driver.get(url)

                # Optional authentication check and handling
                # if self._requires_login():
                #     if not username or not password:
                #         self.logger.warning(f"Skipping {url} - authentication required but credentials not provided")
                #         return
                #     self.login_to_website(url, username, password)

                initial_analysis = self.analyze_page(context=url)
                self.execute_test_cycle(initial_analysis)
                self.track_navigation(url)
                return self.generate_report()
                
        finally:
            if self.driver:
                self.driver.quit()

    def process_single_url(self, url, username, password):
        """
        Process individual URL with existing workflow
        
        Args:
            url (str): URL to process
            username (str): Optional username for authentication
            password (str): Optional password for authentication
        """
        self.logger.info(f"\n{'='*50}")
        self.logger.info(f"Processing URL: {url}")
        
        try:
            self.driver.get(url)
            
            # Optional authentication check and handling
            # if self._requires_login():
            #     if not username or not password:
            #         self.logger.warning(f"Skipping {url} - authentication required but credentials not provided")
            #         return
            #     self.login_to_website(url, username, password)
            
            analysis = self.analyze_page(context=url)
            self.execute_test_cycle(analysis)
            self.track_navigation(url)
            
        except Exception as e:
            self.logger.error(f"Failed to process URL {url}: {str(e)}")

    def _requires_login(self):
        """Use LLM to check if login/registration is required"""
        try:
            #page_html = self.driver.page_source[:5000]
            page_html = self.driver.page_source
            system_prompt = self.prompt_manager.get_prompt("requires_auth", "system")
            user_prompt_template = self.prompt_manager.get_prompt("requires_auth", "user")
            # Format prompt with dynamic values
            user_prompt = user_prompt_template.format(
                url=self.driver.current_url,
                page_html=page_html
            )
            result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")
            try:
                # Extract JSON from potential text explanation
                json_str = result
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].strip()

                parsed= json.loads(json_str)
                self.logger.debug(f"Sanitized LLM response for login/signup check: {parsed}")
                return parsed.get('requires_auth', False)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response: {str(e)}")
                return {}
            #result = json.loads(response.choices[0].message.content)
            #return result.get('requires_auth', False)
            
        except Exception as e:
            self.logger.error(f"LLM auth check failed: {str(e)}, using fallback")
            # Fallback to element detection
            return any([
                self.element_exists(By.CSS_SELECTOR, "input[type='password'], #login, #signup, #register"),
                self.element_exists(By.XPATH, "//*[contains(text(), 'Log in') or contains(text(), 'Sign up')]")
            ])
    
    def element_exists(self, by, value):
        try:
            self.driver.find_element(by, value)
            return True
        except NoSuchElementException:
            return False
        
    ## Dynamic with LLM Analysis
    def login_to_website(self, url, username=None, password=None):
        """Perform dynamic login/registration with user input for additional fields"""
        if not username or not password:
            raise ValueError("Credentials required for authentication")
            
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            
            #page_html = self.driver.page_source[:10000]
            page_html = self.driver.page_source
            system_prompt = self.prompt_manager.get_prompt("auth_form_selectors", "system")
            user_prompt_template = self.prompt_manager.get_prompt("auth_form_selectors", "user")
            # Format prompt with dynamic values
            user_prompt = user_prompt_template.format(
                page_html=page_html
            )
            result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")
            
            #auth_data = json.loads(response.choices[0].message.content)
            try:
                # Extract JSON from potential text explanation
                json_str = result
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].strip()

                self.logger.debug(f"Sanitized LLM response: {json_str}")
                auth_data= json.loads(json_str)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse LLM response: {str(e)}")
                return {}
            #auth_data = json.loads(result)
            self.logger.debug(f"Auth form structure: {json.dumps(auth_data, indent=2)}")

            # Fill credentials
            self.driver.find_element(By.CSS_SELECTOR, auth_data['username_selector']).send_keys(username)
            self.driver.find_element(By.CSS_SELECTOR, auth_data['password_selector']).send_keys(password)

            # Handle additional fields
            if 'additional_fields' in auth_data:
                field_values = {}
                for field_name, field_info in auth_data['additional_fields'].items():
                    while True:
                        value = input(f"Enter {field_name} ({field_info.get('type', 'text')}): ")
                        if self.validate_field_input(value, field_info.get('type')):
                            field_values[field_name] = value
                            break
                        print(f"Invalid format for {field_name}. Please try again.")
                    
                    self.driver.find_element(By.CSS_SELECTOR, field_info['selector']).send_keys(field_values[field_name])

            # Submit form
            self.driver.find_element(By.CSS_SELECTOR, auth_data['submit_selector']).click()
            
            WebDriverWait(self.driver, 10).until(
                lambda d: d.current_url != url
            )
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse auth selectors: {str(e)}")
            raise RuntimeError("Failed to analyze login form structure")
        except NoSuchElementException as e:
            self.logger.error(f"Auth element not found: {str(e)}")
            raise RuntimeError("Authentication elements missing on page")
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise

    def validate_field_input(self, value, field_type):
        """Basic validation for different field types"""
        if not value:
            return False
            
        if field_type == "email":
            return '@' in value and '.' in value.split('@')[-1]
        elif field_type == "tel":
            return value.replace(' ', '').replace('-', '').isdigit()
        elif field_type == "date":
            return bool(re.match(r'\d{4}-\d{2}-\d{2}', value))
        return True

    def track_navigation(self, base_url):
        """Track navigation changes and analyze new pages"""
        current_url = self.driver.current_url
        while True:
            try:
                WebDriverWait(self.driver, 30).until(
                    lambda d: d.current_url != current_url
                )
                
                new_url = self.driver.current_url
                if new_url in self.visited_pages or new_url == base_url:
                    break
                    
                self.visited_pages.add(new_url)
                page_analysis = self.analyze_page(context=new_url)
                self.execute_test_cycle(page_analysis)
                current_url = new_url
                
            except TimeoutException:
                self.logger.info("Navigation tracking completed")
                break

    def generate_report(self):
        """Generate test execution report"""
        report = {
            'start_time': datetime.now().isoformat(),
            'pages_visited': list(self.visited_pages),
            'test_results': self.test_results,
            'success_rate': (len([r for r in self.test_results if r['result']['success']]) / 
                           len(self.test_results) if self.test_results else 0),
            'generated_scripts': [f for f in os.listdir('test_scripts') 
                                if f.endswith(('.py', '.java'))] if os.path.exists('test_scripts') else []
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/test_report_{timestamp}.json"
        
        if not os.path.exists('reports'):
            os.makedirs('reports')
            
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report_file

    def _log_test_result(self, result):
        """Log test execution result"""
        self.test_results.append({
            'timestamp': datetime.now().isoformat(),
            'url': self.driver.current_url,
            'result': result
        })

    def _validate_auth_test_data_usage(self, test_cases, test_data):
        """Validate that generated auth tests use provided test data"""
        for tc in test_cases:
            if 'auth' in tc.get('type', ''):
                if not self._contains_test_data_values(tc, test_data):
                    self.logger.debug(f"Test case '{tc['name']}' doesn't use provided test data")
                else:
                    self.logger.debug(f"Test case '{tc['name']}' has properly used provided test data")

    def _contains_test_data_values(self, test_case, test_data):
        """Check if test case uses appropriate values from test data"""
        if 'test_data' not in test_case:
            return False
            
        test_fields = set(test_case['test_data'].keys())
        
        for section in test_data:
            if section == 'registration_fields':
                fields = set(test_data['registration_fields'].keys())
                if test_fields <= fields:
                    for field in test_fields:
                        allowed_values = (
                            test_data['registration_fields'][field]['valid'] +
                            test_data['registration_fields'][field]['invalid'] +
                            [""]
                        )
                        if test_case['test_data'][field] not in allowed_values:
                            return False
                    return True
            elif 'valid' in test_data[section] and isinstance(test_data[section]['valid'], dict):
                fields = set(test_data[section]['valid'].keys())
                if test_fields <= fields:
                    for field in test_fields:
                        allowed_values = [
                            test_data[section]['valid'][field],
                            test_data[section]['invalid'][field],
                            ""
                        ]
                        if test_case['test_data'][field] not in allowed_values:
                            return False
                    return True
        return False
