"""
Main Web Test Generator module
"""

import os
import json
import re
import subprocess
import tempfile
import tldextract
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
                                      ElementClickInterceptedException)
from webdriver_manager.chrome import ChromeDriverManager
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime
from jsonschema import validate, ValidationError

from .llm_wrapper import LLMWrapper
from .prompt_manager import PromptManager
from .url_extractor import URLExtractor
from ..utils.logging_utils import setup_logger

from ..db.database import init_db, SessionLocal
from sqlalchemy import func
from ..tables.page import Page
from ..tables.test_case_data import TestCase
from ..tables.domain import Domain

from bs4 import BeautifulSoup, Comment

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
                 wait_time="", testing_tool="selenium", language="python", llm_provider_choice=1):
        """
        Initialize WebTestGenerator
        
        Args:
            log_level (str): Logging level
            selenium_version (str): Selenium version for generated scripts
            wait_time (str): Custom wait time for CAPTCHA handling
            testing_tool (str): Testing framework to use
            language (str): Programming language for test scripts
            llm_provider_choice (int): LLM provider choice (1=OpenAI, 2=Groq, 3=Google-Gemini, 4=Anthropic, 5=Ollama)
        """ 
        self.log_level = log_level.upper()
        self.selenium_version = selenium_version
        self.wait_time = wait_time
        self.testing_tool = testing_tool.lower()

        # Initialize DB on startup
        self.initialize_database() 
        
        # Validate language support
        valid_langs = SUPPORTED_LANGUAGES.get(testing_tool.lower(), [])
        if language.lower() not in valid_langs:
            raise ValueError(
                f"'{language}' not supported for {testing_tool}. "
                f"Valid options: {', '.join(valid_langs)}"
            )
        
        self.language = language.lower()
        
        # Initialize components with provider choice
        self.llm = LLMWrapper(llm_provider_choice=llm_provider_choice)
        self.prompt_manager = PromptManager()
        self.driver = None
        self.visited_pages = set()
        self.test_results = []
        self.logger = setup_logger("WebTestGenerator", log_level)
        self.temperature = 0.3
        self.auth_data = {}
        #self.extract_test_relevant_html()
        
        # Setup browser and URL extractor
        self.setup_browser()
        self.url_extractor = URLExtractor(self.driver, self.logger)

        self._generation_interrupted = False

    def initialize_database(self):
        init_db()  # Create tables if they don’t exist 

    def setup_browser(self):
        """Setup Chrome browser with headless configuration"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = Service()
        # service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def capture_screenshot(self):
        """Capture and return base64 encoded screenshot"""
        screenshot = self.driver.get_screenshot_as_png()
        img = Image.open(BytesIO(screenshot))
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    # @staticmethod
    # def extract_test_relevant_html(page_source):
    #     soup = BeautifulSoup(page_source, "html.parser")
    #     # Remove scripts, styles, meta, and comments
    #     for tag in soup(["script", "style", "meta"]):
    #         tag.decompose()
    #     # Optionally, remove comments and whitespace
    #     for element in soup(text=lambda text: isinstance(text, Comment)):
    #         element.extract()
    #     # Extract only forms, buttons, inputs, links, tables, selects, textareas
    #     relevant = []
    #     for tag in ["form", "input", "button", "a", "select", "table", "textarea"]:
    #         relevant.extend(soup.find_all(tag))
    #     # Convert back to string, limit to N elements per type if needed
    #     relevant_html = "\n".join(str(el) for el in relevant[:20])  # cap at 20 elements/type
    #     return relevant_html

    @staticmethod
    def extract_test_relevant_html(page_source):
        soup = BeautifulSoup(page_source, "html.parser")

        # Remove non-interactive and unnecessary tags
        tags_to_remove = [
            "script",       # JavaScript code
            "meta",         # Metadata about the document
            "link",         # External resources (CSS, favicon, etc.)
            "style",        # CSS styling
            "noscript",     # Content for when JavaScript is disabled
            #"base",         # Base URL for relative links
            #"head",         # Document head section (if you want to remove entirely)
            "title",        # Page title (if not needed for testing)
            "svg",          # SVG graphics (unless testing graphics)
            "canvas",       # Canvas elements (unless testing graphics)
            "audio",        # Audio elements (unless testing media)
            "video",        # Video elements (unless testing media)
            "source",       # Media source elements
            "track",        # Text tracks for media elements
            "embed",        # Embedded content
            "object",       # Object elements
            "param",        # Parameters for objects
            "iframe",       # Inline frames (unless testing embedded content)
            "frame",        # Frame elements (deprecated)
            "frameset",     # Frameset elements (deprecated)
            "noframes",     # No frames content (deprecated)
            "applet",       # Java applets (deprecated)
            "area",         # Image map areas (unless testing image maps)
            "map",          # Image maps (unless testing image maps)
            "wbr",          # Line break opportunities
            "bdi",          # Bidirectional isolation (unless testing i18n)
            "bdo",          # Bidirectional override (unless testing i18n)
            "ruby",         # Ruby annotations (unless testing typography)
            "rt",           # Ruby text
            "rp",           # Ruby parentheses
            "details",      # Disclosure widget (unless testing interactive elements)
            "summary",      # Summary for details element
            "dialog",       # Dialog boxes (unless testing modals)
            "menu",         # Context menus (unless testing menus)
            "menuitem",     # Menu items (deprecated)
            "datalist",     # Data list options (unless testing form suggestions)
            "progress",     # Progress indicators (unless testing progress)
            "meter",        # Scalar measurements (unless testing measurements)
            "template",     # Template elements
            "slot",         # Web component slots
            "output",       # Form output (unless testing form calculations)
            "math",         # MathML content (unless testing math)
            "annotation-xml" # MathML annotations
        ]

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
        
    def analyze_page(self, regenerate, first_time, context="current", require_login=False, username=None, password=None):
        """
        Analyze current page and generate metadata
        
        Args:
            regenerate (bool): Whether to regenerate the test data
            context (str): Context description for logging
            
        Returns:
            dict: Page analysis results with metadata, test cases, and scripts
        """
        if regenerate or first_time:
            self.logger.debug(f"Analyzing {context} page...")
            page_source = self.driver.page_source
            
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
            minimized_html = self.extract_test_relevant_html(page_source)
            #minimized_html = page_source
            llm_metadata = self.llm_page_analysis(minimized_html)
            self.logger.debug(f"LLM extracted page metadata: {llm_metadata}")
            
            # Combine static and dynamic metadata
            page_metadata = {**static_metadata, **llm_metadata}
            # page_metadata = llm_metadata
            self.logger.debug(f"Combined page metadata: {page_metadata}")
            
            # Generate test cases and scripts
            test_cases = self.generate_page_specific_tests(page_metadata, minimized_html)
            extracted = tldextract.extract(context)
            domain_name = f"{extracted.domain}.{extracted.suffix}"
            with SessionLocal() as db:
                # Check if domain is already in database or not
                domain_exists = db.query(Domain).filter(Domain.domain_name == domain_name).first()
                if not domain_exists:
                    # If not, add it to database
                    new_domain = Domain(domain_name=domain_name)
                    db.add(new_domain)
                    db.commit()
                    db.refresh(new_domain)
                    domain_id = new_domain.id
                else:
                    domain_id = domain_exists.id
                    
                page = db.query(Page).filter(Page.page_url == context).first()
                if not page:
                    page = Page(page_url = context)
                    db.add(page)

                page.domain_id = domain_id
                page.page_title = self.driver.title   
                page.page_source = minimized_html
                page.page_metadata = page_metadata
                page.test_cases = test_cases
                page.test_cases_count = len(test_cases)
                
                db.commit()
                db.refresh(page)

            # scripts = [self.generate_script_for_test_case(tc, page_metadata, minimized_html) 
            #           for tc in test_cases]
        else:
            self.logger.debug(f"Fetching data for '{context}' page from database...")
            with SessionLocal() as db:
                page = db.query(Page).filter(Page.page_url == context).first()

                minimized_html = page.page_source
                self.logger.debug(f"Successfully fetched page metadata: {page.page_metadata}")
                page_metadata = page.page_metadata
                # Make a copy of test cases to work with
                test_cases = page.test_cases.copy()  # Create a copy for local manipulation

                self.logger.debug(f"Successfully fetched {page.test_cases_count} test cases")
                self.logger.debug(f"Test Case Details:\n{json.dumps(test_cases, indent=2)}")

                while True:
                    try:
                        user_input = input("\nDo you want to add manual test cases? (y/n): ").strip().lower()
                        self.logger.debug("Do you want to add manual test cases? (y/n): ")
                        self.logger.debug(f"User entered: {user_input}")
                        
                        if user_input in ['y', 'yes']:
                            self.logger.debug("Starting manual test case generation...")
                            manual_test_cases = self.generate_manual_test_cases(page_metadata, minimized_html)
                            
                            if manual_test_cases:
                                self.logger.debug(f"Added {len(manual_test_cases)} manual test cases")
                                self.logger.debug("Manual Test Case Details:\n" + json.dumps(manual_test_cases, indent=2))
                                # page.test_cases.extend(manual_test_cases)

                                # Extend the local test_cases list
                                test_cases.extend(manual_test_cases)
                                
                                # Update the database within the session
                                page.test_cases = test_cases
                                page.test_cases_count = len(test_cases)
                                db.commit()
                                db.refresh(page)

                                self.logger.debug(f"Database updated with {len(manual_test_cases)} new manual test cases")
                            else:
                                self.logger.debug("No manual test cases were added")
                            # break
                            
                        elif user_input in ['n', 'no']:
                            self.logger.debug("Skipping manual test case generation")
                            break
                            
                        else:
                            self.logger.debug("Invalid input. Please enter 'y' for yes or 'n' for no")
                            continue
                            
                    except KeyboardInterrupt:
                        self.logger.debug("\nManual test case prompt interrupted by user.")
                        break

                # Final logging with updated count
                self.logger.debug(f"Final test case count: {len(test_cases)}")
                self.logger.debug(f"Final Test Case Details:\n{json.dumps(test_cases, indent=2)}")

            # self.logger.debug(f"Successfully fetched {page.test_cases_count} test cases")
            test_cases = page.test_cases
            #self.logger.debug(f"Test Case Details:\n {page.test_cases}")
            # self.logger.debug("Test Case Details:")
            # for i, test_case in enumerate(page.test_cases, 1):
            #     self.logger.debug(f"Test Case {i}: {test_case}")
            # self.logger.debug(f"Test Case Details:\n{json.dumps(page.test_cases, indent=2)}")
            #self.logger.debug("Test Case Details:\n" + json.dumps(page.test_cases, indent=2))
                
            

        # Manual intervention for script generation
        self.logger.debug(f"Updated Test Cases:\n{json.dumps(test_cases, indent=2)}")
        scripts, selected_test_cases = self.generate_scripts_with_manual_intervention(test_cases, page_metadata, minimized_html, regenerate, require_login, username, password)
        
        return {
            "metadata": page_metadata,
            "test_cases": test_cases,
            "scripts": scripts,
            "selected_test_cases": selected_test_cases
        }
    

    def generate_scripts_with_manual_intervention(self, test_cases, page_metadata, minimized_html, regenerate, require_login, username, password):
        """
        Generate scripts with manual intervention - user selects which test cases to generate scripts for

        Args:
            test_cases (list): List of test cases
            page_metadata (dict): Page metadata
            minimized_html (str): Minimized HTML content

        Returns:
            tuple: (scripts, selected_test_cases) - Generated scripts and corresponding test cases
        """
        if not test_cases:
            self.logger.debug("No test cases found to generate scripts for.")
            return [], []

        scripts = []
        selected_test_cases = []  # Track which test cases were selected
        # Display test cases with serial numbers
        self.logger.debug("="*60)
        self.logger.debug("\t\t\t\t\tAVAILABLE TEST CASES:")
        self.logger.debug("="*60)
        for i, test_case in enumerate(test_cases, 1):
            self.logger.debug(f"{i}. {test_case.get('name', 'Unnamed Test Case')}")
            self.logger.debug(f"   Type: {test_case.get('type', 'N/A')}")
            self.logger.debug(f"   Test Case Type: {test_case.get('test_case_type', 'N/A')}")
            self.logger.debug(f"   Steps: {len(test_case.get('steps', []))} step(s)")
            
            # Display complete steps
            steps = test_case.get('steps', [])
            if steps:
                self.logger.debug(f"   Steps:")
                for j, step in enumerate(steps, 1):
                    self.logger.debug(f"     {j}. {step}")
            else:
                self.logger.debug(f"   Steps: No steps defined")
            
            # Display validation
            validation = test_case.get('validation', '')
            if validation:
                self.logger.debug(f"   Validation: {validation}")
            else:
                self.logger.debug(f"   Validation: No validation defined")
            print()

        while True:
            try:
                user_input = input("Enter test case number(s), 'all', 'list' to show cases, 'delete' to remove a case, 'edit' to edit a case, or 'quit' to stop: ").strip()
                self.logger.debug("Enter test case number(s), 'all', 'list' to show cases, 'delete' to remove a case, 'edit' to edit a case, or 'quit' to stop: ")
                self.logger.debug(f"User entered: {user_input}")

                if user_input.lower() == 'quit':
                    self.logger.debug("Script generation stopped by user.")
                    break

                if user_input.lower() == 'list':
                    self.logger.debug("="*60)
                    self.logger.debug("\t\t\t\t\tAVAILABLE TEST CASES:")
                    self.logger.debug("="*60)
                    for i, test_case in enumerate(test_cases, 1):
                        self.logger.debug(f"{i}. {test_case.get('name', 'Unnamed Test Case')}")
                        self.logger.debug(f"   Type: {test_case.get('type', 'N/A')}")
                        self.logger.debug(f"   Test Case Type: {test_case.get('test_case_type', 'N/A')}")
                        self.logger.debug(f"   Steps: {len(test_case.get('steps', []))} step(s)")
                        
                        # Display complete steps
                        steps = test_case.get('steps', [])
                        if steps:
                            self.logger.debug(f"   Steps:")
                            for j, step in enumerate(steps, 1):
                                self.logger.debug(f"     {j}. {step}")
                        else:
                            self.logger.debug(f"   Steps: No steps defined")
                        
                        # Display validation
                        validation = test_case.get('validation', '')
                        if validation:
                            self.logger.debug(f"   Validation: {validation}")
                        else:
                            self.logger.debug(f"   Validation: No validation defined")
                        print()
                    continue

                if user_input.lower() == 'delete':
                    # Call the delete_test_case method
                    self.delete_test_case(test_cases, page_metadata)
                    # After deletion, refresh the display and continue
                    continue

                if user_input.lower() == 'edit':
                    self.edit_test_case(test_cases, page_metadata, regenerate=regenerate)
                    continue

                # Handle "all" input
                if user_input.lower() == 'all':
                    test_case_numbers = list(range(1, len(test_cases) + 1))
                    self.logger.debug(f"Processing all test cases: {test_case_numbers}")
                else:
                    # Handle comma-separated input
                    try:
                        test_case_numbers = [int(num.strip()) for num in user_input.split(',')]
                        
                        # Validate all numbers are within range
                        invalid_numbers = [num for num in test_case_numbers if num < 1 or num > len(test_cases)]
                        if invalid_numbers:
                            self.logger.debug(f"Invalid test case number(s): {invalid_numbers}. Please enter numbers between 1 and {len(test_cases)}")
                            continue
                            
                    except ValueError:
                        self.logger.debug("Invalid input. Please enter valid numbers separated by commas, 'all', 'list', 'delete', 'edit' or 'quit'")
                        continue

                # Process each selected test case
                for test_case_num in test_case_numbers:
                    selected_test_case = test_cases[test_case_num - 1]
                    
                    with SessionLocal() as db:
                        test_case = db.query(TestCase).filter(
                            (TestCase.page_url == self.driver.current_url) & (TestCase.test_case_data == selected_test_case)
                        ).first()
                        if test_case and not regenerate:
                            self.logger.debug(f"Test script already exists for test case {test_case_num}: '{selected_test_case.get('name', 'Unnamed Test Case')}' at {test_case.script_path}")
                            self.logger.debug(f"Skipping existing script for test case {test_case_num}: '{selected_test_case.get('name', 'Unnamed Test Case')}'")
                            # For "all" or multiple selections, auto-skip existing scripts unless regenerating
                            if len(test_case_numbers) > 1:
                                if selected_test_case in selected_test_cases:
                                    self.logger.debug(f"Test script stored: {test_case.script_path}")
                                    self.logger.debug(f"✓ Script fetched successfully for test case {test_case_num} from the database")
                                else:
                                    filename = os.path.basename(test_case.script_path)
                                    selected_test_cases.append(selected_test_case)
                                    scripts.append({'script': test_case.test_script, 'filename': filename})
                                    self.logger.debug(f"Test script stored: {test_case.script_path}")
                                    self.logger.debug(f"✓ Script fetched successfully for test case {test_case_num} from the database")
                            else:
                                # Single test case - ask user for regeneration
                                while True:
                                    regen_input = input("Do you want to regenerate the script for the selected test case? (y/n): ").strip()
                                    self.logger.debug("Do you want to regenerate the script for the selected test case? (y/n): ")
                                    self.logger.debug(f"User entered: {regen_input}")
                                    
                                    if regen_input.lower() == 'y':
                                        self.logger.debug(f"Regenerating script for: {selected_test_case.get('name', 'Unnamed Test Case')}")
                                        self.logger.debug("Please wait...")
                                        script, filename, script_path = self.generate_script_for_test_case(selected_test_case, page_metadata, minimized_html, require_login, username, password)
                                        
                                        if script:
                                            test_case.page_url = self.driver.current_url
                                            test_case.test_case_title = selected_test_case.get('name', 'Unnamed Test Case')
                                            test_case.test_case_type = selected_test_case.get('type', 'N/A')
                                            test_case.test_case_data = selected_test_case
                                            test_case.test_script = script
                                            test_case.script_path = script_path
                                            db.commit()
                                            db.refresh(test_case)
                                            scripts.append({'script': script, 'filename': filename})
                                            selected_test_cases.append(selected_test_case)
                                            self.logger.debug(f"✓ Script generated successfully for test case {test_case_num}")
                                            break
                                        else:
                                            self.logger.debug(f"✗ Failed to generate script for test case {test_case_num}")
                                            continue
                                    
                                    elif regen_input.lower() == 'n':
                                        self.logger.debug("Skipping script regeneration")
                                        self.logger.debug(f"Fetching script for: '{selected_test_case.get('name', 'Unnamed Test Case')}' from database")
                                        self.logger.debug("Please wait...")
                                        self.logger.debug(f"Test script stored: {test_case.script_path}")
                                        self.logger.debug(f"✓ Script fetched successfully for test case {test_case_num} from the database")
                                        break
                                    else:
                                        self.logger.debug("Invalid input. Please enter 'y' or 'n'")
                                        continue
                        if not test_case or regenerate:
                            if selected_test_case in selected_test_cases:
                                self.logger.debug(f"Test script stored: {test_case.script_path}")
                                self.logger.debug(f"✓ Script fetched successfully for test case {test_case_num} from the database")
                            # Generate new script
                            else:
                                self.logger.debug(f"Generating script for test case {test_case_num}: {selected_test_case.get('name', 'Unnamed Test Case')}")
                                self.logger.debug("Please wait...")
                                script, filename, script_path = self.generate_script_for_test_case(selected_test_case, page_metadata, minimized_html, require_login, username, password)
                                
                                if script:
                                    test_case = TestCase(
                                        page_url=self.driver.current_url,
                                        test_case_title=selected_test_case.get('name', 'Unnamed Test Case'),
                                        test_case_type=selected_test_case.get('type', 'N/A'),
                                        test_case_data=selected_test_case,
                                        test_script=script,
                                        script_path=script_path
                                    )
                                    
                                    db.add(test_case)
                                    db.commit()
                                    db.refresh(test_case)
                                    scripts.append({'script': script, 'filename': filename})
                                    selected_test_cases.append(selected_test_case)
                                    self.logger.debug(f"✓ Script generated successfully for test case {test_case_num}")
                                else:
                                    self.logger.debug(f"✗ Failed to generate script for test case {test_case_num}")

                # If processing multiple test cases, break the main loop after processing
                if len(test_case_numbers) == len(test_cases):
                    break

            except KeyboardInterrupt:
                self.logger.debug("\n\nScript generation interrupted by user.")
                # Set a flag to indicate interruption occurred
                self._generation_interrupted = True
                break
            except Exception as e:
                self.logger.error(f"Error during script generation: {str(e)}")
                continue

        return scripts, selected_test_cases
    
    def delete_test_case(self, test_cases, page_metadata):
        """
        Delete a test case from the list and update the database accordingly
        Args:
            test_cases (list): List of current test cases
            page_metadata (dict): Current page metadata
        """
        while True:
            try:
                del_input = input("Enter the test case number you want to delete or 'cancel' to abort deletion: ").strip()
                self.logger.debug("Enter the test case number you want to delete or 'cancel' to abort deletion: ")
                self.logger.debug(f"User entered: {del_input}")

                if del_input.lower() == 'cancel':
                    self.logger.debug("Deletion cancelled by user.")
                    break

                del_index = int(del_input)
                if del_index < 1 or del_index > len(test_cases):
                    self.logger.debug(f"Invalid test case number: {del_index}. Must be between 1 and {len(test_cases)}")
                    continue

                # Confirm deletion
                test_case_name = test_cases[del_index - 1].get('name', 'Unnamed Test Case')
                confirm = input(f"Are you sure you want to delete test case #{del_index} - '{test_case_name}'? (y/n): ").strip().lower()
                self.logger.debug(f"Confirm deletion of test case #{del_index} - '{test_case_name}' (y/n): ")
                self.logger.debug(f"User entered: {confirm}")
                
                if confirm != 'y':
                    self.logger.debug("Deletion aborted by user.")
                    break

                # Remove from local list
                deleted_case = test_cases.pop(del_index - 1)
                self.logger.debug(f"Deleted test case: {deleted_case.get('name', 'Unnamed Test Case')}")

                # Update the database
                with SessionLocal() as db:
                    # Find and delete matching TestCase record(s) for this page and test case data
                    test_case_db = db.query(TestCase).filter(
                        (TestCase.page_url == self.driver.current_url) &
                        (TestCase.test_case_data == deleted_case)
                    ).first()

                    self.logger.debug(f"TestCase table url: {TestCase.page_url}")
                    self.logger.debug(f"Driver url: {self.driver.current_url}")
                    
                    if test_case_db:
                        db.delete(test_case_db)
                        self.logger.debug(f"Removed test case from TestCase table in database")

                    # Update Page test_cases and test_cases_count
                    # normalized_url = self.driver.current_url.rstrip('/')
                    # page = db.query(Page).filter(Page.page_url == normalized_url).first()

                    # Determine if normalization should be applied based on Page.page_url in the database
                    candidate_page = db.query(Page).filter(Page.page_url == self.driver.current_url.rstrip('/')).first()
                    if candidate_page and not candidate_page.page_url.endswith('/'):
                        normalized_url = self.driver.current_url.rstrip('/')
                        page = db.query(Page).filter(Page.page_url == normalized_url).first()
                    else:
                        page = db.query(Page).filter(Page.page_url == self.driver.current_url).first()

                    if page:
                        page.test_cases = test_cases
                        page.test_cases_count = len(test_cases)
                        db.commit()
                        db.refresh(page)
                        self.logger.debug(f"Updated Page record with new test cases count: {len(test_cases)}")

                # After deletion, show updated list count
                self.logger.debug(f"Test case #{del_index} deleted successfully. Remaining test cases: {len(test_cases)}")
                print(f"✓ Test case #{del_index} deleted successfully. Remaining test cases: {len(test_cases)}")
                break

            except ValueError:
                self.logger.debug("Invalid input. Please enter a valid number or 'cancel'.")
                print("Invalid input. Please enter a valid number or 'cancel'.")
                continue
            except Exception as e:
                self.logger.error(f"Error during test case deletion: {str(e)}")
                print(f"Error during test case deletion: {str(e)}")
                break

    def edit_test_case(self, test_cases, page_metadata, regenerate=False):
        """
        Edit a test case if script is not generated OR if regenerate is True.
        Args:
            test_cases (list): Current list of test cases
            page_metadata (dict): Current page metadata
            regenerate (bool): If True, allow editing even if a script is present
        """
        while True:
            try:
                edit_input = input("Enter test case number to edit or 'cancel' to abort: ").strip()
                self.logger.debug("Enter test case number to edit or 'cancel' to abort: ")
                self.logger.debug(f"User entered: {edit_input}")

                if edit_input.lower() == 'cancel':
                    self.logger.debug("Edit cancelled by user.")
                    break

                edit_index = int(edit_input)
                if edit_index < 1 or edit_index > len(test_cases):
                    self.logger.debug(f"Invalid test case number: {edit_index}. Must be between 1 and {len(test_cases)}")
                    continue

                selected_test_case = test_cases[edit_index - 1]

                # --- Use same normalized url approach ---
                with SessionLocal() as db:
                    # Fetch possible script for this test case
                    # normalized_url = self.driver.current_url.rstrip('/')
                    # candidate_page = db.query(Page).filter(Page.page_url == normalized_url).first()
                    # page_url_to_use = normalized_url if candidate_page and not candidate_page.page_url.endswith('/') else self.driver.current_url

                    # test_case_rec = db.query(TestCase).filter(
                    #     (TestCase.page_url == page_url_to_use) & (TestCase.test_case_data == selected_test_case)
                    # ).first()

                    # script_exists = test_case_rec is not None and test_case_rec.test_script

                    candidate_page = db.query(Page).filter(Page.page_url == self.driver.current_url.rstrip('/')).first()
                    if candidate_page and not candidate_page.page_url.endswith('/'):
                        page_url_to_use = self.driver.current_url.rstrip('/')
                    else:
                        page_url_to_use = self.driver.current_url

                    test_case_db = db.query(TestCase).filter(
                        (TestCase.page_url == page_url_to_use) & (TestCase.test_case_data == selected_test_case)
                    ).first()

                    script_exists = test_case_db is not None and test_case_db.test_script

                # Only allow if script does not exist or if regenerate is True
                if script_exists and not regenerate:
                    print("Editing not allowed: Script already generated for this test case.")
                    self.logger.debug("Editing not allowed: Script already generated for this test case.")
                    break

                # Display the full test case content
                print("Current test case data (in JSON):\n")
                print(json.dumps(selected_test_case, indent=2))
                print("\nEnter revised test case in JSON (multi-line; empty line to finish).")

                # Collect new test case content
                lines = []
                while True:
                    line = input()
                    if line.strip() == "":
                        break
                    lines.append(line)

                if not lines:
                    print("Edit aborted: No input provided.")
                    self.logger.debug("Edit aborted: No input provided.")
                    break

                new_content = '\n'.join(lines)
                self.logger.debug(f"User entered: {new_content}")
                try:
                    new_test_case = json.loads(new_content)
                except Exception as exc:
                    print("Invalid JSON. Please try again.")
                    self.logger.debug(f"Invalid JSON entered during edit: {exc}")
                    continue

                # Mark edited test case as manual
                new_test_case['test_case_type'] = 'manual'

                # Update the list and DB
                test_cases[edit_index - 1] = new_test_case

                with SessionLocal() as db:
                    page_obj = db.query(Page).filter(Page.page_url == page_url_to_use).first()
                    if page_obj:
                        page_obj.test_cases = test_cases
                        db.commit()
                        db.refresh(page_obj)
                        self.logger.debug(f"Updated Page.test_cases after edit for #{edit_index}")

                print(f"✓ Test case #{edit_index} - '{test_cases[edit_index - 1].get('name', 'Unnamed Test Case')}' edited successfully.")
                self.logger.debug(f"✓ Test case #{edit_index} - '{test_cases[edit_index - 1].get('name', 'Unnamed Test Case')}' edited successfully.")
                break

            except ValueError:
                print("Invalid input. Please enter a valid number or 'cancel'.")
                continue
            except Exception as e:
                print(f"Error during test case edit: {str(e)}")
                self.logger.error(f"Error during test case edit: {str(e)}")
                break


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
            test_data = self.load_test_data()
            self.logger.debug(f"Test Data: {test_data}")
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

    def generate_page_specific_tests(self, page_metadata, minimized_html):
        """
        Generate context-aware test cases based on page content
        
        Args:
            page_metadata (dict): Page metadata
            minimized_html (str): HTML source of the page
            
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
            self.logger.debug("Sending request to LLM for test case generation...")
            system_prompt = self.prompt_manager.get_prompt("generate_tests", "system")
            user_prompt_template = self.prompt_manager.get_prompt("generate_tests", "user")
            
            user_prompt = user_prompt_template.format(
                page_metadata=json.dumps(page_metadata, indent=2),
                prompt_suffix=prompt_suffix_new,
                title=self.driver.title,
                forms=json.dumps(page_metadata['forms']),
                buttons=json.dumps(page_metadata['buttons']),
                interactive_elements=json.dumps(page_metadata.get('interactive_elements', [])),
                #interactive_elements = json.dumps(page_metadata['interactive_elements']),
                ui_validation_indicators=json.dumps(page_metadata.get('ui_validation_indicators', [])),
                url=page_metadata['url'],
                page_source=minimized_html
            )
            
            result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")
            # self.logger.debug(f"Raw LLM response: {result}")
            self.logger.debug("Received response from LLM")
            
            try:
                # Parse JSON response
                json_str = result
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].strip()
                    
                parsed = json.loads(json_str)
                auto_test_cases = parsed['test_cases']

                # Mark auto-generated test cases
                for test_case in auto_test_cases:
                    test_case['test_case_type'] = 'auto-generated'
                
                self.logger.debug(f"Successfully parsed {len(auto_test_cases)} auto-generated test cases")
                self.logger.debug("Auto-Generated Test Case Details:\n" + json.dumps(auto_test_cases, indent=2))

                # Ask user if they want to add manual test cases
                while True:
                    try:
                        user_input = input("\nDo you want to add manual test cases? (y/n): ").strip().lower()
                        self.logger.debug("Do you want to add manual test cases? (y/n): ")
                        self.logger.debug(f"User entered: {user_input}")
                        
                        if user_input in ['y', 'yes']:
                            self.logger.debug("Starting manual test case generation...")
                            manual_test_cases = self.generate_manual_test_cases(page_metadata, minimized_html)
                            
                            if manual_test_cases:
                                self.logger.debug(f"Added {len(manual_test_cases)} manual test cases")
                                self.logger.debug("Manual Test Case Details:\n" + json.dumps(manual_test_cases, indent=2))
                                auto_test_cases.extend(manual_test_cases)
                            else:
                                self.logger.debug("No manual test cases were added")
                            # break
                            
                        elif user_input in ['n', 'no']:
                            self.logger.debug("Skipping manual test case generation")
                            break
                            
                        else:
                            self.logger.debug("Invalid input. Please enter 'y' for yes or 'n' for no")
                            continue
                            
                    except KeyboardInterrupt:
                        self.logger.debug("\nManual test case prompt interrupted by user.")
                        break
                
                # Validate test data usage
                # if test_data:
                #     # self._validate_auth_test_data_usage(parsed.get('test_cases', []), test_data)
                #     self._validate_auth_test_data_usage(auto_test_cases, test_data)

                # Log all test case details
                self.logger.debug(f"Successfully parsed {len(auto_test_cases)} total test cases")
                self.logger.debug("All Test Case Details:\n" + json.dumps(auto_test_cases, indent=2))
                    
                return auto_test_cases
            
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON for test cases: {str(e)}")
                # Print the problematic part of the JSON (20 chars before and after)
                start = max(e.pos - 40, 0)
                end = min(e.pos + 40, len(json_str))
                error_snippet = json_str[start:end]
                self.logger.debug(f"\n🔍 Error context:\n...{error_snippet}...")
                self.logger.debug(f"Raw response: {result}")
                return {"test_cases": []}
        except Exception as e:
            self.logger.error(f"Test generation failed: {str(e)}")
            return []
        
    # def generate_manual_test_cases(self, page_metadata, minimized_html):
    #     """
    #     Allow users to manually add test cases via CLI prompts
        
    #     Args:
    #         page_metadata (dict): Page metadata
    #         minimized_html (str): HTML source of the page
            
    #     Returns:
    #         list: Manually generated test cases
    #     """
    #     manual_test_cases = []
        
    #     while True:
    #         try:
    #             user_prompt = input("\nEnter your test case description (or 'done' to finish): ").strip()
    #             self.logger.debug(f"Manual test case prompt: {user_prompt}")
                
    #             if user_prompt.lower() in ['done', 'exit', 'quit']:
    #                 break
                    
    #             if not user_prompt:
    #                 self.logger.debug("Please enter a valid test case description.")
    #                 continue
                    
    #             # Generate test case using LLM
    #             manual_test_case = self._generate_single_manual_test_case(user_prompt, page_metadata, minimized_html)
                
    #             if manual_test_case:
    #                 manual_test_cases.append(manual_test_case)
    #                 self.logger.debug(f"✓ Manual test case added: {manual_test_case.get('name', 'Unnamed Test Case')}")
    #             else:
    #                 self.logger.debug("✗ Failed to generate test case. Please try again.")
                    
    #         except KeyboardInterrupt:
    #             self.logger.debug("\nManual test case addition interrupted by user.")
    #             break
    #         except Exception as e:
    #             self.logger.error(f"Error during manual test case generation: {str(e)}")
    #             continue
                
    #     return manual_test_cases

    def generate_manual_test_cases(self, page_metadata, minimized_html):
        """
        Allow users to manually add test cases via CLI prompts
        
        Args:
            page_metadata (dict): Page metadata
            minimized_html (str): HTML source of the page
            
        Returns:
            list: Manually generated test cases
        """
        manual_test_cases = []
        
        while True:
            try:
                self.logger.debug("\nEnter your test case description (press Enter on empty line to finish, or 'done' to stop adding test cases):")
                print("Enter your test case description (press Enter on empty line to finish, or 'done' to stop adding test cases):")
                
                # Collect multi-line input
                lines = []
                while True:
                    try:
                        line = input()
                        if line.strip().lower() in ['done', 'exit', 'quit']:
                            # If user types 'done', exit the entire method
                            self.logger.debug(f"User entered: {line}")
                            return manual_test_cases
                        elif line.strip() == "":
                            # Empty line means user is finished with this test case description
                            break
                        else:
                            lines.append(line)
                    except EOFError:
                        # Handle Ctrl+D (EOF)
                        break
                
                # Join all lines into a single prompt
                user_prompt = '\n'.join(lines).strip()
                self.logger.debug(f"Manual test case prompt: {user_prompt}")
                
                if not user_prompt:
                    self.logger.debug("No test case description provided. Please enter a valid description.")
                    print("No test case description provided. Please enter a valid description.")
                    continue
                    
                # Generate test case using LLM
                manual_test_case = self._generate_single_manual_test_case(user_prompt, page_metadata, minimized_html)
                
                if manual_test_case:
                    manual_test_cases.append(manual_test_case)
                    self.logger.debug(f"✓ Manual test case added: {manual_test_case.get('name', 'Unnamed Test Case')}")
                    print(f"✓ Manual test case added: {manual_test_case.get('name', 'Unnamed Test Case')}")
                else:
                    self.logger.debug("✗ Failed to generate test case. Please try again.")
                    print("✗ Failed to generate test case. Please try again.")
                    
            except KeyboardInterrupt:
                self.logger.debug("\nManual test case addition interrupted by user.")
                print("\nManual test case addition interrupted by user.")
                break
            except Exception as e:
                self.logger.error(f"Error during manual test case generation: {str(e)}")
                print(f"Error during manual test case generation: {str(e)}")
                continue
                
        return manual_test_cases


    def _generate_single_manual_test_case(self, user_prompt, page_metadata, minimized_html):
        """
        Generate a single manual test case based on user input
        
        Args:
            user_prompt (str): User's test case description
            page_metadata (dict): Page metadata
            minimized_html (str): HTML source of the page
            
        Returns:
            dict: Generated test case or None if failed
        """

        test_data = None
        prompt_suffix_new = ""
        
        # Get prompt suffix templates from YAML
        suffix_templates = self.prompt_manager.get_prompt("generate_manual_test", "prompt_suffix")
        
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
            self.logger.debug("Generating manual test case based on user input...")
            
            system_prompt = self.prompt_manager.get_prompt("generate_manual_test", "system")
            user_prompt_template = self.prompt_manager.get_prompt("generate_manual_test", "user")
            
            formatted_user_prompt = user_prompt_template.format(
                user_test_description=user_prompt,
                page_metadata=json.dumps(page_metadata, indent=2),
                prompt_suffix=prompt_suffix_new,
                title=self.driver.title,
                url=page_metadata['url'],
                page_source=minimized_html
            )
            
            result = self.llm.generate(system_prompt, formatted_user_prompt, model_type="analysis")
            self.logger.debug("Received response from LLM for manual test case")
            
            # Parse JSON response
            json_str = result
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                json_str = result.split("```")[1].strip()
                
            parsed = json.loads(json_str)
            test_case = parsed.get('test_case', {})
            # test_case = parsed['test_case']
            
            # Mark as manual test case
            test_case['test_case_type'] = 'manual'
            
            return test_case
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON for manual test case: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Manual test case generation failed: {str(e)}")
            return None
        
    def generate_script_for_test_case(self, test_case, page_metadata, minimized_html, require_login, username, password):
        """
        Generate test script for a specific test case
        
        Args:
            test_case (dict): Test case specification
            page_metadata (dict): Page metadata
            minimized_html (str): HTML source of the page
            
        Returns:
            tuple: (script_content, filename) - Generated test script code and saved filename
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
            
            if require_login and username and password:
                login_instructions = "yes"
            else:
                login_instructions = "no"

            user_prompt = user_prompt_template.format(
                language=self.language,
                selenium_version=self.selenium_version,
                test_case=json.dumps(test_case, indent=2),
                page_metadata=json.dumps(page_metadata, indent=2),
                page_source=minimized_html,
                captcha_wait_time=captcha_wait_time,
                login_instructions=login_instructions,
                username=username,
                password=password,
                auth_data=self.auth_data,
                security_indicators=page_metadata.get('security_indicators', [])
            )
            
            script_content = self.llm.generate(system_prompt, user_prompt, model_type="selenium")
            # self.logger.debug(f"Raw LLM response generated code: {script_content}")
            
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

            filename = None
            
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
                    #script_name = f"{script_dir}/test_{timestamp}_{sanitized_name}.py"
                    filename = f"test_{timestamp}_{sanitized_name}.py"
                else:
                    #script_name = f"{script_dir}/test_{timestamp}_{sanitized_name}.java"
                    filename = f"test_{timestamp}_{sanitized_name}.java"

                script_path = f"{script_dir}/{filename}"

                # with open(script_name, 'w') as f:
                #     f.write(code)
                with open(script_path, 'w') as f:
                    f.write(code)

                self.logger.debug(f"LLM generated test script:\n{code}")   
                self.logger.debug(f"Saved test script: {script_path}")
                
            return code, filename, script_path
            
        except Exception as e:
            self.logger.error(f"Script generation failed: {str(e)}")
            return "", None

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
        self.logger.debug(f"Saved test script: {script_name}")

    def execute_test_cycle(self, analysis):
        """Execute test cycle for page analysis results"""
        # Check if generation was interrupted
        if hasattr(self, '_generation_interrupted') and self._generation_interrupted:
            self.logger.debug("Test cycle execution skipped due to user interruption")
            return
        scripts = analysis['scripts']
        selected_test_cases = analysis.get('selected_test_cases', [])

        # for i, script in enumerate(scripts):
        #     if not self.validate_script_structure(script):
        #         continue

        #     # Get corresponding test case name
        #     # test_name = analysis['test_cases'][i]['name'] if i < len(analysis['test_cases']) else f"Test_{i+1}"

        #     # Get corresponding test case name from selected test cases
        #     test_name = selected_test_cases[i]['name'] if i < len(selected_test_cases) else f"Test_{i+1}"

        #     # Generate file name (you might want to store this when creating the script)
        #     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        #     sanitized_name = re.sub(r'[^a-zA-Z0-9\-_]', '_', test_name)
        #     sanitized_name = re.sub(r'_+', '_', sanitized_name)
        #     sanitized_name = sanitized_name.strip('_')
        #     file_name = f"test_{timestamp}_{sanitized_name}.py"

        #     result = self.execute_test_script(script)
        #     self._log_test_result(result, test_name, file_name)

        for i, script_info in enumerate(scripts):
            script_content = script_info['script'] if isinstance(script_info, dict) else script_info
            filename = script_info.get('filename') if isinstance(script_info, dict) else None
            
            if not self.validate_script_structure(script_content):
                continue

            test_name = selected_test_cases[i]['name'] if i < len(selected_test_cases) else f"Test_{i+1}"
            
            # Use stored filename or generate fallback
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                sanitized_name = re.sub(r'[^a-zA-Z0-9\-_]', '_', test_name)
                sanitized_name = re.sub(r'_+', '_', sanitized_name)
                sanitized_name = sanitized_name.strip('_')
                filename = f"test_{timestamp}_{sanitized_name}.py"

            result = self.execute_test_script(script_content)
            self._log_test_result(result, test_name, filename)

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

            # Combine stdout and stderr for comprehensive analysis
            combined_output = result.stdout + result.stderr

            # Analyze output for test failure indicators
            test_passed = self._analyze_test_output(combined_output, result.returncode)
            
            return {
                #'success': result.returncode == 0,
                'success': test_passed,
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

    def _analyze_test_output(self, combined_output, return_code):
        """
        Analyze test output to determine if test actually passed or failed using LLM with fallback
        
        Args:
            combined_output (str): Combined stdout and stderr
            return_code (int): Process return code
            
        Returns:
            bool: True if test passed, False if failed
        """

        # First try LLM analysis
        try:
            llm_result = self._analyze_test_output_with_llm(combined_output, return_code)
            if llm_result is not None:
                self.logger.debug(f"LLM determined test result: {'passed' if llm_result else 'failed'}")
                return llm_result
        except Exception as e:
            self.logger.warning(f"LLM test output analysis failed: {str(e)}, falling back to keyword analysis")
        
        # Fallback to existing keyword and return code analysis
        self.logger.debug("Using fallback keyword and return code analysis")

        # Convert to lowercase for case-insensitive matching
        output_lower = combined_output.lower()
        
        # Explicit failure indicators (highest priority)
        failure_indicators = [
            '[error] fail',
            'fail:',
            'failed:',
            'test failed',
            'assertion failed',
            'assertionerror',
            'validation result: false',
            'valid: false',
            'does not display correct',
            'does not match expected',
            'element not found',
            'timeout',
            'exception:',
            '[error]',
            'failed'
        ]
        
        # Check for explicit failure indicators
        # for indicator in failure_indicators:
        #     if indicator in output_lower:
        #         self.logger.debug(f"Test failed due to indicator: {indicator}")
        #         return False
        
        # Explicit success indicators
        success_indicators = [
            'pass:',
            'passed:',
            'test passed',
            'success:',
            'all tests passed',
            'validation successful',
            'test completed successfully',
            'test completed:'
        ]
        
        # Check for explicit success indicators
        for indicator in success_indicators:
            if indicator in output_lower:
                self.logger.debug(f"Test passed due to indicator: {indicator}")
                return True
            
        # Check for explicit failure indicators
        for indicator in failure_indicators:
            if indicator in output_lower:
                self.logger.debug(f"Test failed due to indicator: {indicator}")
                return False
        
        # If no explicit indicators found, fall back to return code
        # Return code 0 typically means success, non-zero means failure
        if return_code == 0:
            self.logger.debug("Test passed based on return code 0")
            return True
        else:
            self.logger.debug(f"Test failed based on return code {return_code}")
            return False
        
    def _analyze_test_output_with_llm(self, combined_output, return_code):
        """
        Use LLM to analyze test output for success/failure determination
        Args:
            combined_output (str): Combined stdout and stderr
            return_code (int): Process return code
        Returns:
            bool or None: True if test passed, False if failed, None if analysis failed
        """
        try:
            system_prompt = self.prompt_manager.get_prompt("test_output_analysis", "system")
            user_prompt_template = self.prompt_manager.get_prompt("test_output_analysis", "user")
            
            user_prompt = user_prompt_template.format(
                test_output=combined_output,
                return_code=return_code
            )
            
            self.logger.debug("Sending test output to LLM for analysis...")
            result = self.llm.generate(system_prompt, user_prompt, model_type="result_analysis")
            
            # Parse JSON response
            json_str = result
            if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                json_str = result.split("```")[1].strip()
            
            parsed = json.loads(json_str)
            test_passed = parsed.get('test_passed', None)
            reasoning = parsed.get('reasoning', 'No reasoning provided')
            
            self.logger.debug(f"LLM analysis result: {test_passed}, reasoning: {reasoning}")
            
            return test_passed
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse LLM test analysis response: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"LLM test output analysis failed: {str(e)}")
            return None

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

    def run_workflow(self, url, username=None, password=None, no_cache=False, recursive=False, max_depth=1):
        """
        Main workflow execution with optional recursive URL discovery
        
        Args:
            url (str): URL to test
            username (str): Optional username for authentication
            password (str): Optional password for authentication
            no_cache (bool): Whether to use cache memory (database) or not
            recursive (bool): Whether to perform recursive URL extraction
            max_depth (int): Maximum depth for recursive extraction
            
        Returns:
            list or str: List of paths to generated report files when recursive=True, 
            single path string when recursive=False
        """
        try:
            if recursive:
                # Enhanced workflow with recursive URL discovery
                all_urls = self.url_extractor.extract_urls(url, max_depth=max_depth)
                if not all_urls:
                    self.logger.warning("No URLs found to test")
                    return self.generate_report()
                
                # Display all extracted URLs with index numbers
                self.logger.debug("="*60)
                self.logger.debug("\t\t\t\tEXTRACTED URLS:")
                self.logger.debug("="*60)
                for i, extracted_url in enumerate(all_urls, 1):
                    self.logger.debug(f"{i}. {extracted_url}")
                print()

                reports = []
                # Process each URL
                # for discovered_url in all_urls:
                #     self.process_single_url(discovered_url, username, password, no_cache)
                #     report_path = self.generate_report()
                #     reports.append(report_path)
                    # self.logger.debug(f"Test Report generated at: {report_path}")

                while True:
                    try:
                        user_input = input("Enter URL number(s), 'all', 'list' to show URLs, or 'quit' to stop: ").strip()
                        self.logger.debug("Enter URL number(s), 'all', 'list' to show URLs, or 'quit' to stop: ")
                        self.logger.debug(f"User entered: {user_input}")
                        
                        if user_input.lower() == 'quit':
                            self.logger.debug("URL processing stopped by user.")
                            break
                            
                        if user_input.lower() == 'list':
                            self.logger.debug("="*60)
                            self.logger.debug("\t\t\t\tEXTRACTED URLS:")
                            self.logger.debug("="*60)
                            for i, extracted_url in enumerate(all_urls, 1):
                                self.logger.debug(f"{i}. {extracted_url}")
                            print()
                            continue
                            
                        # Handle "all" input
                        if user_input.lower() == 'all':
                            url_numbers = list(range(1, len(all_urls) + 1))
                            self.logger.debug(f"Processing all URLs: {url_numbers}")
                        else:
                            # Handle comma-separated input
                            try:
                                url_numbers = [int(num.strip()) for num in user_input.split(',')]
                                
                                # Validate all numbers are within range
                                invalid_numbers = [num for num in url_numbers if num < 1 or num > len(all_urls)]
                                if invalid_numbers:
                                    self.logger.debug(f"Invalid URL number(s): {invalid_numbers}. Please enter numbers between 1 and {len(all_urls)}")
                                    continue
                                    
                            except ValueError:
                                self.logger.debug("Invalid input. Please enter valid numbers separated by commas, 'all', 'list', or 'quit'")
                                continue
                        
                        # Process each selected URL
                        for url_num in url_numbers:
                            selected_url = all_urls[url_num - 1]
                            self.logger.debug(f"Processing URL {url_num}: {selected_url}")
                            self.process_single_url(selected_url, username, password, no_cache)
                            report_path = self.generate_report()
                            reports.append(report_path)
                            self.logger.debug(f"✓ URL {url_num} processed successfully")
                        
                        # If processing multiple URLs, break the main loop after processing
                        if len(url_numbers) == len(all_urls):
                            break
                            
                    except KeyboardInterrupt:
                        self.logger.debug("\n\nURL processing interrupted by user.")
                        break
                    except Exception as e:
                        self.logger.error(f"Error during URL processing: {str(e)}")
                        continue
                    
                #return self.generate_report()
                return reports  # Return list of all report paths
            else:
                # Original single-page workflow
                self.driver.get(url)
                if not no_cache:
                    with SessionLocal() as db:
                        page = db.query(Page).filter(Page.page_url == url and Page.page_source == self.driver.page_source).first()
                        if page:
                            self.logger.debug(f"Provided webpage: '{url}' is already tested and validated...!!!")
                            regenerate = False
                            first_time = False
                        else:
                            self.logger.debug("Detected a new webpage. Proceeding with the analysis...")
                            regenerate = False
                            first_time = True
                else:
                    self.logger.debug("Cache is disabled. Proceeding with the analysis...")
                    regenerate = True  
                    first_time = False
                # Optional authentication check and handling
                require_login=False
        
                if self.driver.current_url != url:
                    if self._requires_login():
                        self.logger.debug(f"Authentication required for page '{url}'")
                        if not username or not password:
                            self.logger.warning(f"Skipping {url} - authentication required but credentials not provided")
                            return
                        self.login_to_website(url, username, password) 
                        require_login = True
                    
                initial_analysis = self.analyze_page(regenerate=regenerate, first_time=first_time, context=url, require_login=require_login, username=username, password=password)
                self.execute_test_cycle(initial_analysis)
                self.track_navigation(url)
                return self.generate_report()
                
        finally:
            if self.driver:
                self.driver.quit()

    def process_single_url(self, url, username, password, no_cache):
        """
        Process individual URL with existing workflow
        
        Args:
            url (str): URL to process
            username (str): Optional username for authentication
            password (str): Optional password for authentication
            no_cache (bool): Whether to use cache memory (database) or not
        """
        self.logger.debug(f"\n{'='*50}")
        self.logger.debug(f"Processing URL: {url}")
        
        try:
            self.driver.get(url)
            require_login=False
            if not no_cache:
                with SessionLocal() as db:
                    page = db.query(Page).filter(Page.page_url == url and Page.page_source == self.driver.page_source).first()
                    if page:
                        self.logger.debug(f"Provided webpage: '{url}' is already tested and validated...!!!")
                        regenerate = False
                        first_time = False
                        #return 
                    else:
                        self.logger.debug("Detected a new webpage. Proceeding with the analysis...")
                        regenerate = False
                        first_time = True
            else:
                self.logger.debug("Cache is disabled. Proceeding with the analysis...")
                regenerate = True 
                first_time = False
            # Optional authentication check and handling
            require_login=False
  
            if self.driver.current_url != url:
                if self._requires_login():
                    self.logger.debug(f"Authentication required for page '{self.driver.current_url}'")
                    if not username or not password:
                        self.logger.warning(f"Skipping {url} - authentication required but credentials not provided")
                        return
                    self.login_to_website(url, username, password) 
                    require_login = True
            
            analysis = self.analyze_page(regenerate=regenerate, first_time=first_time, context=url, require_login=require_login, username=username, password=password)
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
            self.logger.debug(f"Authentication in progress...")
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
            # Parse LLM response
            try:
                json_str = result
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].strip()
                    
                auth_data = json.loads(json_str)
                self.auth_data = auth_data
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
                        self.logger.debug(f"Invalid format for {field_name}. Please try again.")
                    
                    self.driver.find_element(By.CSS_SELECTOR, field_info['selector']).send_keys(field_values[field_name])

            # Submit form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, auth_data['submit_selector'])
            try:
                submit_button.click()
            except ElementClickInterceptedException:
                self.logger.debug("Click intercepted, attempting JavaScript click...")
                self.driver.execute_script("arguments[0].click();", submit_button)
            
            # Wait for potential redirection (up to 10 seconds)
            WebDriverWait(self.driver, 10).until(
                EC.url_changes(self.driver.current_url)
            )
            
            # Get the redirected URL
            redirected_url = self.driver.current_url
            self.logger.debug(f"Redirected to: {redirected_url}")
            
            # Check if redirected URL matches the provided URL
            if redirected_url == url:
                self.logger.debug("Redirection matches the provided URL. Authentication successful...!")
            else:
                self.logger.debug(f"Redirected URL: '{redirected_url}' does not match provided URL: '{url}'. Navigating to provided URL...")
                # Navigate to the provided URL using the same session
                self.driver.get(url)
                
                # Validate that the page has loaded the correct URL
                WebDriverWait(self.driver, 10).until(
                    EC.url_to_be(url)
                )
                if self.driver.current_url == url:
                    self.logger.debug(f"Successfully navigated to provided URL: {url}")
                    self.logger.debug("Authentication and navigation successful...!")
                else:
                    self.logger.error(f"Failed to navigate to provided URL: {url}. Current URL: {self.driver.current_url}")
                    raise RuntimeError("Failed to load the provided URL after redirection")   
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse auth selectors: {str(e)}")
            raise RuntimeError("Failed to analyze login form structure")
        except NoSuchElementException as e:
            self.logger.error(f"Auth element not found: {str(e)}")
            raise RuntimeError("Authentication elements missing on page")
        except TimeoutException as e:
            self.logger.error(f"Timeout during redirection or navigation: {str(e)}")
            raise RuntimeError("Failed to detect redirection or navigate to the provided URL")
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
                self.logger.debug("Navigation tracking completed")
                break

    def generate_report(self):
        """Generate test execution report"""
        report = {
            'start_time': datetime.now().isoformat(),
            'pages_visited': list(self.visited_pages),
            'test_results': self.test_results,
            'success_rate': (len([r for r in self.test_results if r['result']['success']]) / 
                           len(self.test_results) if self.test_results else 0),
            # 'generated_scripts': [f for f in os.listdir('test_scripts') 
            #                     if f.endswith(('.py', '.java'))] if os.path.exists('test_scripts') else [],
            'generated_scripts': list(set([r['file_name'] for r in self.test_results if r['file_name']])),

            'test_summary': [
                {
                    'test_name': r['test_name'],
                    'file_name': r['file_name'],
                    'success': r['result']['success'],
                    'timestamp': r['timestamp']
                }
                for r in self.test_results
            ]
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/test_report_{timestamp}.json"
        
        if not os.path.exists('reports'):
            os.makedirs('reports')
            
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        self.logger.debug(f"Test Report generated at: {report_file}")    
        return report_file

    def _log_test_result(self, result, test_name=None, file_name=None):
        """Log test execution result"""

        try:
            current_url = self.driver.current_url if self.driver else "Unknown (Driver terminated)"
        except Exception:
            current_url = "Unknown (Driver connection lost)"

        self.test_results.append({
            'timestamp': datetime.now().isoformat(),
            #'url': self.driver.current_url,
            'url': current_url,
            'test_name': test_name,
            'file_name': file_name,
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
