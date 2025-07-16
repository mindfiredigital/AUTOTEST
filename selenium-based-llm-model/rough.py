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
import groq
import openai
import base64
from io import BytesIO
from PIL import Image
import argparse
import logging
from datetime import datetime
from jsonschema import validate, ValidationError
#from parse_llm_code import extract_first_code
#from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential

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

load_dotenv()

class ContextFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'test_cases'):
            record.test_cases = []
        return True
    
#from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
import yaml

# Hardcoded test cases in JSON format
test_cases = [
    {
      "name": "Header text 'Login' is styled correctly",
      "type": "ui-validation",
      "steps": [
        "Navigate to https://www.ourgoalplan.co.in/Login.aspx",
        "Locate the header text 'Login'"
      ],
      "selectors": {
        "header_text": ".headerText"
      },
      "validation": "Header text uses correct font-family, font-size, font-weight, color, text-align, and line-height",
      "test_data": {}
    }
]

# Hardcoded page metadata in JSON format
page_metadata = {'title': 'Login | www.ourgoalplan.co.in', 'url': 'https://www.ourgoalplan.co.in/Login.aspx', 'forms': [{'id': 'Form2', 'action': 'https://www.ourgoalplan.co.in/Login.aspx', 'method': 'post', 'inputs': [{'type': 'hidden', 'name': '__EVENTTARGET', 'id': '__EVENTTARGET'}, {'type': 'hidden', 'name': '__EVENTARGUMENT', 'id': '__EVENTARGUMENT'}, {'type': 'hidden', 'name': '__VIEWSTATE', 'id': '__VIEWSTATE'}, {'type': 'hidden', 'name': '__VIEWSTATEGENERATOR', 'id': '__VIEWSTATEGENERATOR'}, {'type': 'hidden', 'name': '__SCROLLPOSITIONX', 'id': '__SCROLLPOSITIONX'}, {'type': 'hidden', 'name': '__SCROLLPOSITIONY', 'id': '__SCROLLPOSITIONY'}, {'type': 'hidden', 'name': '__EVENTVALIDATION', 'id': '__EVENTVALIDATION'}, {'type': 'text', 'name': 'txtName', 'id': 'txtName'}, {'type': 'password', 'name': 'txtPassword', 'id': 'txtPassword'}, {'type': 'checkbox', 'name': 'chkRemember', 'id': 'chkRemember'}, {'type': 'submit', 'name': 'btnLogin', 'id': 'btnLogin'}], 'buttons': []}], 'buttons': [{'tag': 'input', 'text': '', 'id': '__EVENTTARGET', 'type': 'hidden'}, {'tag': 'input', 'text': '', 'id': '__EVENTARGUMENT', 'type': 'hidden'}, {'tag': 'input', 'text': '', 'id': '__VIEWSTATE', 'type': 'hidden'}, {'tag': 'input', 'text': '', 'id': '__VIEWSTATEGENERATOR', 'type': 'hidden'}, {'tag': 'input', 'text': '', 'id': '__SCROLLPOSITIONX', 'type': 'hidden'}, {'tag': 'input', 'text': '', 'id': '__SCROLLPOSITIONY', 'type': 'hidden'}, {'tag': 'input', 'text': '', 'id': '__EVENTVALIDATION', 'type': 'hidden'}, {'tag': 'input', 'text': '', 'id': 'txtName', 'type': 'text'}, {'tag': 'input', 'text': '', 'id': 'txtPassword', 'type': 'password'}, {'tag': 'a', 'text': 'Forgot Password', 'id': 'lnkBtnResetPassword', 'type': ''}, {'tag': 'input', 'text': '', 'id': 'chkRemember', 'type': 'checkbox'}, {'tag': 'input', 'text': '', 'id': 'btnLogin', 'type': 'submit'}, {'tag': 'a', 'text': 'Mindfire Solutions', 'id': '', 'type': ''}], 'tables': [], 'key_flows': {'main_navigation': [], 'primary_actions': []}, 'auth_requirements': {'auth_required': True, 'auth_type': 'login', 'auth_fields': [{'name': 'txtName', 'type': 'text', 'required': True, 'selector': '#txtName', 'validation_indicators': [{'type': 'element', 'value': '#lblValidation', 'description': "Validation message displayed in span with id 'lblValidation' if input is invalid"}, {'type': 'alert', 'value': 'JS alert via ValidateTextBoxes()', 'description': "JavaScript function 'ValidateTextBoxes()' likely triggers alert or message on invalid input"}], 'default_value': ''}, {'name': 'txtPassword', 'type': 'password', 'required': True, 'selector': '#txtPassword', 'validation_indicators': [{'type': 'element', 'value': '#lblValidation', 'description': "Validation message displayed in span with id 'lblValidation' if input is invalid"}, {'type': 'masking', 'value': 'masked', 'description': 'Input is masked as password'}, {'type': 'alert', 'value': 'JS alert via ValidateTextBoxes()', 'description': "JavaScript function 'ValidateTextBoxes()' likely triggers alert or message on invalid input"}], 'default_value': ''}, {'name': 'chkRemember', 'type': 'checkbox', 'required': False, 'selector': '#chkRemember', 'validation_indicators': [], 'default_value': 'checked'}], 'credentials_hint': ''}, 'contact_form_fields': [], 'interactive_elements': [{'type': 'button', 'text': 'Login', 'selector': '#btnLogin', 'action': 'submit', 'expected_outcome': 'Submits login form; triggers ValidateTextBoxes() for validation', 'sub_elements': []}, {'type': 'link', 'text': 'Forgot Password', 'selector': '#lnkBtnResetPassword', 'action': 'click', 'expected_outcome': "Triggers __doPostBack('lnkBtnResetPassword',''); likely initiates password reset flow", 'sub_elements': []}, {'type': 'checkbox', 'text': 'Stay Logged In', 'selector': '#chkRemember', 'action': 'click', 'expected_outcome': "Toggles 'Stay Logged In' state", 'sub_elements': []}, {'type': 'link', 'text': 'Logo image', 'selector': '#imgLogo', 'action': 'click', 'expected_outcome': 'No link present; image only', 'sub_elements': []}, {'type': 'link', 'text': 'Mindfire Solutions', 'selector': '.footerStyle a', 'action': 'click', 'expected_outcome': 'Redirects to http://www.mindfiresolutions.com (opens in new tab)', 'sub_elements': []}], 'ui_validation_indicators': [{'element_selector': '#lblValidation', 'validation_type': 'state_change', 'validation_value': 'validation message', 'description': 'Displays validation errors for login fields'}, {'element_selector': '#txtPassword', 'validation_type': 'masking', 'validation_value': 'masked', 'description': 'Password input is masked'}], 'main_content': "Login form with username, password, and 'Stay Logged In' option. Includes 'Forgot Password' link and site logo. Footer credits Mindfire Solutions.", 'key_actions': ['Login with username and password', 'Request password reset', "Toggle 'Stay Logged In' option"], 'content_hierarchy': {'primary_sections': ['Header (Logo)', 'Login Form', 'Footer'], 'subsections': ['Username input', 'Password input', 'Forgot Password link', 'Stay Logged In checkbox', 'Login button', 'Validation message']}, 'security_indicators': ['csrf_token']}

# Hardcoded page source as a string
page_source = """
<html><head id="HeaderLogin"><title> Login | www.ourgoalplan.co.in </title></head><body id="body1"><form action="./Login.aspx" id="Form2" method="post" name="Form2"><div><input id="__EVENTTARGET" name="__EVENTTARGET" type="hidden" value=""/><input id="__EVENTARGUMENT" name="__EVENTARGUMENT" type="hidden" value=""/><input id="__VIEWSTATE" name="__VIEWSTATE" type="hidden" value="Uc7+HNQOAYMBJn1GwyWy5rNNUC3G7oHYXK9+qKdG1HLxJjQH2ThQ0gIZ/1CiUfrBUYkHOQ9ct+5qYVVYsju2InFLVu7c75dzIMcDAeIvvO3KvBLFiRbiXEudy7HPnerAwwgAont4fIv3gFCdIxaHH4KUCB/DXUWS14IPPXFTp5I="/></div><div><input id="__VIEWSTATEGENERATOR" name="__VIEWSTATEGENERATOR" type="hidden" value="C2EE9ABB"/><input id="__SCROLLPOSITIONX" name="__SCROLLPOSITIONX" type="hidden" value="0"/><input id="__SCROLLPOSITIONY" name="__SCROLLPOSITIONY" type="hidden" value="0"/><input id="__EVENTVALIDATION" name="__EVENTVALIDATION" type="hidden" value="pkSJv/dyxn4SxKtxSf6TRc//EH89xztQWT3FPHt0xBTKbb9E73hNFOH3oR5LLDebpcHLJPfHAAtYV/qRS4rOXd4vpwxPITf/y9GnTW9DDcoKkxC7/KNJEcaMj0Zm4+yPigRrMFwYTI199d8Wr4vJOKOLvCVkBLjVQSIXKm/NjZRbwE4nx867yqwLtS+NxGgGl25WGfiD0vTwnQN1OGnmRw=="/></div><div class="container-fluid"><div align="center"><img id="imgLogo" src="Images/goalplan_small.jpg" style="border-width:0px;"/><br/></div><div class="form-container"><p class="text-primary headerText">Login</p><div class="form-group"><input class="input-medium" id="txtName" name="txtName" placeholder="Username" type="text"/></div><div class="form-group" style="margin-bottom: 5px;"><input class="input-medium" id="txtPassword" name="txtPassword" placeholder="Password" type="password"/></div><div class="row" style="margin-bottom: 15px;"><div class="col-sm-6" id="divResetPassword"><a class="forgotPasswordLinkStyle" href="javascript:__doPostBack('lnkBtnResetPassword','')" id="lnkBtnResetPassword">Forgot Password</a></div><div class="col-sm-6" id="divStayLoggedIn"><label class="switch"><input checked="checked" id="chkRemember" name="chkRemember" type="checkbox"/><span class="slider round"></span><div class="toggleText">Stay Logged In</div></label></div></div><div class="form-group"><input class="btn btn-danger loginButtonStyle" id="btnLogin" name="btnLogin" onclick="return ValidateTextBoxes();" type="submit" value="Login"/></div><div class="form-group validationMessageContainer"><span class="validationMessageStyle" id="lblValidation"></span></div></div><div align="center" class="footerStyle"> © <a href="http://www.mindfiresolutions.com" target="_blank">Mindfire Solutions</a> | 2005 - 2025. <br/></div></div></form></body></html>
"""

class LLMWrapper:
    def __init__(self, config_path="llm_config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
            
        self.provider = self.config["model_provider"]
        #self.model = self._initialize_model()
        self.models = self._initialize_models()

    def _initialize_models(self):
        provider = self.config["model_provider"]
        params = self.config["model_settings"].get(provider, {})

        # Get API key based on provider
        api_key = os.getenv(
            "OPENAI_API_KEY" if provider == "openai" else "GROQ_API_KEY"
        )

        # Correct
        # ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model=..., temperature=...)
        if provider == "openai":
            #return ChatOpenAI(**params)
            return {
            "analysis": ChatOpenAI(api_key=api_key, model=params["analysis_model"], temperature=params["temperature"], model_kwargs={"response_format": {"type": "json_object"}}),
            "selenium": ChatOpenAI(api_key=api_key, model=params["selenium_model"], temperature=params["temperature"])
        }
        elif provider == "groq":
            return {
            "analysis": ChatGroq(api_key=api_key, model=params["analysis_model"], temperature=params["temperature"], model_kwargs={"response_format": {"type": "json_object"}}),
            "selenium": ChatGroq(api_key=api_key, model=params["selenium_model"], temperature=params["temperature"])
        }
        #     return ChatGroq(**params)
        elif provider == "google-gemini":
            return {
                "analysis": ChatGoogleGenerativeAI(api_key=os.getenv("GOOGLE_API_KEY"), model=params["analysis_model"], temperature=params["temperature"], model_kwargs={"response_format": {"type": "json_object"}}),
                "selenium": ChatGoogleGenerativeAI(api_key=os.getenv("GOOGLE_API_KEY"), model=params["selenium_model"], temperature=params["temperature"])
            }
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate(self, system_prompt, user_prompt, model_type="analysis"):
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        #return self.model.invoke(messages).content
        return self.models[model_type].invoke(messages).content

class PromptManager:
    def __init__(self, prompt_file="prompts4.yaml"):
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.prompts = yaml.safe_load(f)

    def get_prompt(self, section, role, tool=None):
        """
        section: e.g., 'llm_page_analysis'
        role: 'system' or 'user'
        """
        #return self.prompts[section][role]
        if tool and section == "generate_script":
            return self.prompts[section][tool][role]
        return self.prompts[section][role]

class WebTestGenerator:
    def __init__(self, log_level="INFO", selenium_version="4.15.2", wait_time="", testing_tool="selenium", language="python"):
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
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.llm = LLMWrapper()
        self.prompt_manager = PromptManager()
        #self.model = "llama-3.3-70b-versatile"
        #self.model = "gpt-4o-2024-08-06"
        #self.selenium_model = "meta-llama/llama-4-maverick-17b-128e-instruct"
        #self.selenium_model = "gpt-4.1-2025-04-14"
        #self.client = groq.Client(api_key=self.groq_api_key)
        #self.client = openai.OpenAI(api_key=self.openai_api_key)
        self.driver = None
        self.visited_pages = set()
        self.test_results = []
        self.logger = self.setup_logging()
        self.temperature = 0.3
        self.setup_browser()
        self.logger.addFilter(ContextFilter())
        self.logger.propagate = False  # Prevent duplicate logs
        self.url_extractor = URLExtractor(self.driver, self.logger)

    def sanitize_filename(filename):
        """
        Replace special characters with underscores to create valid filenames.
        Keeps alphanumeric characters, hyphens, and underscores.
        """
        # Replace any character that's not alphanumeric, hyphen, or underscore with underscore
        sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '_', filename)
        
        # Optional: Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Optional: Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        return sanitized

    def setup_browser(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        service = Service()
        self.driver = webdriver.Chrome(service=service, options=chrome_options)


    def setup_logging(self):
        # Convert string log level to numeric value
        numeric_level = getattr(logging, self.log_level, logging.INFO)
        
        logger = logging.getLogger("WebTestGenerator")
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
        
        # Create file handler
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs('logs', exist_ok=True)
        log_file = f"logs/test_run_{timestamp}.log"
        
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger


    def capture_screenshot(self):
        screenshot = self.driver.get_screenshot_as_png()
        img = Image.open(BytesIO(screenshot))
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    
    def analyze_page(self, context="current"):
        self.logger.info(f"Analyzing {context} page...")
        page_source = self.driver.page_source
        self.logger.info(f"PAGE_SOURCE: {page_source}")
        #page_source = self.driver.page_source[:5000]  # First 5000 characters for LLM context so that it doesn't exceed token limit
        
        # Static metadata extraction
        # page_metadata = {
        #     "title": self.driver.title,
        #     "url": self.driver.current_url,
        #     "forms": self.extract_forms(),
        #     "buttons": self.extract_interactive_elements(),
        #     "tables": self.extract_data_tables(),
        #     "key_flows": self.identify_key_flows()
        # }
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

        test_cases = self.generate_page_specific_tests(page_metadata, page_source)
        scripts = [self.generate_script_for_test_case(tc, page_metadata, page_source) for tc in test_cases]
        
        return {
            "metadata": page_metadata,
            "test_cases": test_cases,
            "scripts": scripts
        }
    
    def llm_page_analysis(self, page_source):
        """Perform dynamic page analysis using LLM"""
        try:
            prompt = f"""Analyze this web page structure and return JSON metadata:
            {{
                "auth_requirements": {{
                    "auth_required": boolean,
                    "auth_type": "login|registration|none",
                    "auth_fields": [
                        {{
                            "name": "username",
                            "type": "email|text|password",
                            "required": boolean
                        }}
                    ]
                }},
                "contact_form_fields": [
                    {{
                        "name": "first name",
                        "type": "text",
                        "required": true
                    }},
                    {{
                        "name": "last name",
                        "type": "text",
                        "required": true
                    }},
                    {{
                        "name": "message",
                        "type": "text",
                        "required": true
                    }},
                    {{
                        "name": "email",
                        "type": "email",
                        "required": true
                    }}
                ],    
                "main_content": "Brief description of main content areas",
                "key_actions": ["list of primary user actions"],
                "content_hierarchy": {{
                    "primary_sections": ["section1", "section2"],
                    "subsections": ["subsection1", "subsection2"]
                }},
                "interactive_patterns": {{
                    "forms": ["login", "search"],
                    "dynamic_elements": ["live_search", "infinite_scroll"]
                }},
                "security_indicators": ["https", "captcha"]
            }}
            
            Current page HTML:
            {page_source}
            
            Focus on:
            - Semantic HTML structure
            - User interaction patterns
            - Content organization
            - Security features
            """
            
            # response = self.client.chat.completions.create(
            #     model=self.model,
            #     messages=[{
            #         "role": "system",
            #         "content": "You are a web page analyst. Extract structural and functional metadata from HTML."
            #     }, {
            #         "role": "user", 
            #         "content": prompt
            #     }],
            #     temperature=0.1,
            #     response_format={"type": "json_object"}
            # )
            #system_prompt = "You are a web page analyst. Extract structural and functional metadata from HTML."
            system_prompt = self.prompt_manager.get_prompt("llm_page_analysis", "system")
            self.logger.debug(f"system prompt for page analysis: {system_prompt}")
            user_prompt_template = self.prompt_manager.get_prompt("llm_page_analysis", "user")
            # Format with actual values
            user_prompt = user_prompt_template.format(
                page_source=page_source  # Preserve formatting
            )
            # user_prompt = self.prompt_manager.get_prompt("llm_page_analysis", "user").format(
            #     page_source=page_source
            # )
            result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")
            #result = response.choices[0].message.content
            self.logger.info("LLM analysis of current page completed")
            self.logger.debug(f"Raw LLM response: {result}")
            try:
                # Extract JSON from potential text explanation
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
        return [{
            "tag": el.tag_name,
            "text": el.text[:50],
            "id": el.get_attribute('id'),
            "type": el.get_attribute('type')
        } for el in self.driver.find_elements(By.CSS_SELECTOR, 'button, a, input, select, textarea')]
    
    def extract_data_tables(self):
        return [{
            "id": table.get_attribute('id'),
            "headers": [th.text for th in table.find_elements(By.TAG_NAME, 'th')],
            "row_count": len(table.find_elements(By.TAG_NAME, 'tr'))
        } for table in self.driver.find_elements(By.TAG_NAME, 'table')]
    
    def identify_key_flows(self):
        return {
            "main_navigation": [a.get_attribute('href') for a in 
                              self.driver.find_elements(By.CSS_SELECTOR, 'nav a, .menu a')[:5]],
            "primary_actions": [btn.text for btn in 
                               self.driver.find_elements(By.CSS_SELECTOR, '.primary-btn, .cta-button')]
        }
    

    def load_test_data(self, file_path="auth_test_data.json"):
        try:
            with open(file_path) as f:
                data = json.load(f)
                
            #validate(data, AUTH_DATA_SCHEMA)
            return data
        except Exception as e:
            self.logger.error(f"Failed to load test data: {str(e)}")
            return None


    def generate_page_specific_tests(self, page_metadata, page_source):
        # Remove schema from prompt to prevent LLM from echoing it back
        """Generate context-aware test cases based on page content for both base functionality and authentication"""
        test_data = None
        # prompt_suffix = ""
        prompt_suffix_new = ""
        # Get prompt suffix templates from YAML
        suffix_templates = self.prompt_manager.get_prompt("generate_tests", "prompt_suffix")

        # Condition 1: Handle auth/contact form test data
        if page_metadata.get('auth_requirements', {}).get('auth_required') or page_metadata.get('contact_form_fields'):
            test_data = self.load_test_data()
            if test_data:
                # Format test_data template from YAML
                test_data_suffix = suffix_templates["test_data"].format(
                    test_data=json.dumps(test_data, indent=2),
                    auth_requirements=json.dumps(page_metadata.get('auth_requirements', {}), indent=2)
                )
                prompt_suffix_new += test_data_suffix

        # Condition 2: Add contact form fields
        if page_metadata.get('contact_form_fields'):
            contact_form_suffix = suffix_templates["contact_form"].format(
                contact_form_fields=json.dumps(page_metadata['contact_form_fields'][0]['fields'], indent=2)
            )
            prompt_suffix_new += contact_form_suffix

        # # Load and format test data if auth required
        # if page_metadata.get('auth_requirements', {}).get('auth_required') or page_metadata.get('contact_form_fields'):
        #     test_data = self.load_test_data()
        #     if test_data:
        #         prompt_suffix = f"""
        #         Available Test Data:
        #         {json.dumps(test_data, indent=2)}
                
        #         For authentication tests:
        #         - Use EXACT values from 'valid' credentials for positive tests
        #         - Use 'invalid' values for negative tests
        #         - Follow field-specific validation rules
        #         - Also test missing values or inputs in required fields for negative tests

        #         Usage Rules for contact_form data (if applicable):
        #         - For contact forms use EXACT values from 'contact_form.valid' for positive tests
        #         - Use 'contact_form.invalid' for negative tests
        #         - Follow field-specific validation rules
        #         - Also test missing values or inputs in required fields for negative tests

        #         Authentication Requirements: 
        #         {json.dumps(page_metadata.get('auth_requirements', {}), indent=2)}
        #         """

        # # Add contact form fields to prompt
        # if page_metadata.get('contact_form_fields'):
        #     prompt_suffix += f"""
        #     When testing for negative cases on contact form fields, properly look for error messages which exist on the page for the respective fields.
        #     Contact Form Fields:
        #     {json.dumps(page_metadata['contact_form_fields'], indent=2)}
        #     """

        # prompt = f"""Generate test cases in VALID JSON format with specific actual current page elements.
        # Generate comprehensive test cases including both regular and authentication tests.
        # Output ONLY valid JSON using this EXACT structure:
        # {{
        #     "test_cases": [
        #         {{
        #             "name": "Test name",
        #             "type": "functional|auth-positive|auth-negative",
        #             "steps": ["step1", "step2"],
        #             "selectors": {{
        #                 "element1": "css_selector",
        #                 "element2": "xpath"
        #             }},
        #             "validation": "Expected outcome",
        #             "test_data": {{
        #                 "field_name": "specific_value"
        #             }}
        #         }}
        #     ]
        # }}
        
        # Current page elements (Page Structure Metadata):
        # {json.dumps(page_metadata, indent=2)}

        # {prompt_suffix}

        # Use selectors from this page structure:
        # {{
        # "title": "{page_metadata['title']}",
        # "forms": {json.dumps(page_metadata['forms'])},
        # "buttons": {json.dumps(page_metadata['buttons'])}
        # }}

        # Current page URL: {page_metadata['url']}
        # Current Page HTML: {page_source}
         
        # Guidelines:
        # 1. Create tests SPECIFIC to these page elements
        # 2. Functional tests for core page elements
        # 3. Cover functional, UI consistency checks, and security aspects
        # 4. Prioritize main user flows
        # 5. Include edge cases for observed input types
        # 6. Include both positive and negative test cases to test functionality
    	 
        # Focus on:
        # - Form validation rules
        # - Navigation consistency
        # - Data presentation integrity
        # - Interactive element functionality
        # - Security considerations
        
        # Rules:
        # 1. Never add comments or explanations
        # 2. Validate JSON before responding
        # 3. Use actual selectors from page metadata
        # 4. For auth tests (if applicable), reference EXACT values from provided test data
        # 5. Auth tests (if auth required):
        #     - Valid credential submission
        #     - Invalid format tests
        #     - Missing required fields
        #     - Security validations
        # 6. Include both positive and negative cases
        
        # Return test cases in specified valid JSON format with Selenium selectors."""
        
        try:
            self.logger.info("Sending request to LLM for test case generation...")
            # response = self.client.chat.completions.create(
            #     model=self.model,
            #     #response_format={"type": "json_object"},
            #     messages=[{
            #         "role": "system", 
            #         "content": "You are a senior QA engineer. Output MUST be valid JSON format as specified. Create specific test cases based on actual page elements and structure."
            #     }, {
            #         "role": "user", 
            #         "content": prompt
            #     }],
            #     temperature=0.1
            # )
            #return self._parse_test_cases(response.choices[0].message.content)
            # system_prompt = """You are a senior QA engineer. Output MUST be valid JSON format as specified. Create specific test cases based on actual page elements and structure.
            # Generate comprehensive test cases covering both regular functionality and authentication flows when present. 
            # Generate test cases using actual authentication test data only when needed and available.
            # Ensure valid JSON output."""
            system_prompt = self.prompt_manager.get_prompt("generate_tests", "system")
            # user_prompt = self.prompt_manager.get_prompt("generate_tests", "user").format(
            #     page_metadata=json.dumps(page_metadata, indent=2),
            #     prompt_suffix=prompt_suffix,
            #     title=page_metadata['title'],
            #     forms=json.dumps(page_metadata['forms']),
            #     buttons=json.dumps(page_metadata['buttons']),
            #     url=page_metadata['url'],
            #     page_source=page_source
            # )
            user_prompt_template = self.prompt_manager.get_prompt("generate_tests", "user")
            # Format with dynamic values
            user_prompt = user_prompt_template.format(
                page_metadata=json.dumps(page_metadata, indent=2),
                prompt_suffix=prompt_suffix_new,
                title=page_metadata['title'],
                forms=json.dumps(page_metadata['forms']),
                buttons=json.dumps(page_metadata['buttons']),
                interactive_elements = json.dumps(page_metadata['interactive_elements']),
                ui_validation_indicators = json.dumps(page_metadata['ui_validation_indicators']),
                url=page_metadata['url'],
                page_source=page_source
            )
            result = self.llm.generate(system_prompt, user_prompt, model_type="analysis")
            #result = response.choices[0].message.content
            self.logger.debug(f"Raw LLM response: {result}")
            self.logger.info("Received response from LLM")
            try:
                # Extract JSON from potential text explanation
                json_str = result
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "```" in result:
                    json_str = result.split("```")[1].strip()
                
                #test_cases = json.loads(json_str)
                parsed = json.loads(json_str)
                test_cases = parsed['test_cases']
                #self.logger.info(f"Successfully parsed {len(test_cases.get('test_cases', []))} test cases")
                self.logger.info(f"Successfully parsed {len(test_cases)} test cases")
                
                # Log the test cases for debugging
                # for tc in test_cases.get('test_cases', []):
                #     self.logger.info(f"Generated test case: {tc['id']} - {tc['name']} ({tc['type']})")
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
        
    def _validate_auth_test_data_usage(self, test_cases, test_data):
        """Ensure generated auth tests use provided test data"""
        for tc in test_cases:
            if 'auth' in tc.get('type', ''):
                if not self._contains_test_data_values(tc, test_data):
                    self.logger.debug(f"Test case '{tc['name']}' doesn't use provided test data")
                else:
                    self.logger.debug(f"Test case '{tc['name']}' has properly used provided test data")
    
    def _contains_test_data_values(self, test_case, test_data):
        """Check if test case uses appropriate values from test data for credentials, contact_form, or registration_fields"""
        test_fields = set(test_case['test_data'].keys())
        
        # Iterate through each section in test_data
        for section in test_data:
            if section == 'registration_fields':
                # For registration_fields, fields are the top-level keys
                fields = set(test_data['registration_fields'].keys())
                if test_fields <= fields:
                    # Validate each field value against allowed values
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
                # For credentials and contact_form, fields are keys in the 'valid' dictionary
                fields = set(test_data[section]['valid'].keys())
                if test_fields <= fields:
                    # Validate each field value against allowed values
                    for field in test_fields:
                        allowed_values = [
                            test_data[section]['valid'][field],
                            test_data[section]['invalid'][field],
                            ""
                        ]
                        if test_case['test_data'][field] not in allowed_values:
                            return False
                    return True
        
        # Return False if no matching section is found
        return False
        
    # def generate_page_specific_tests(self, page_metadata, page_source):
    #     # Existing test generation
    #     base_tests = self.generate_page_specific_base_tests(page_metadata, page_source)
        
    #     # Auth-specific tests
    #     auth_tests = []
    #     if page_metadata.get('auth_requirements', {}).get('auth_required'):
    #         test_data = self.load_test_data()
    #         auth_tests = self._generate_auth_tests(page_metadata, test_data)
        
    #     return base_tests + auth_tests

    def generate_script_for_test_case(self, test_case, page_metadata, page_source):
        captcha_wait_time = self.wait_time or "30 seconds"
        # prompt = f"""Generate Python Selenium script for the following test cases:
        # {json.dumps(test_case, indent=2)}
        
        # Page Structure:
        # {json.dumps(page_metadata, indent=2)}

        # Current page HTML:
        # {page_source}
        
        # Use reliable selectors from page structure.
        # IMPORTANT - Use EXACTLY this WebDriver setup for Selenium 4.15.2:
        # ```
        # from selenium import webdriver
        # from selenium.webdriver.chrome.service import Service
        # from webdriver_manager.chrome import ChromeDriverManager
        
        # # This is the correct way to initialize Chrome in Selenium 4.15.2
        # service = Service(ChromeDriverManager().install())
        # driver = webdriver.Chrome(service=service)
        # ```
        
        # DO NOT use: webdriver.Chrome(ChromeDriverManager().install()) directly as it will cause errors

        # **Before starting any test steps, wait for all JavaScript and AJAX on the page to finish loading.**
        # - Use a robust method such as:
        #     - Waiting for `document.readyState == 'complete'`
        #     - Waiting for jQuery/AJAX activity to finish if present

        # Include CAPTCHA handling when present:
        #     1. Security Features: {page_metadata.get('security_indicators', [])}
        #     2. Check for common CAPTCHA selectors (#captcha, .g-recaptcha, etc.)
        #     3. If CAPTCHA detected:
        #         - Print clear instructions for manual solving
        #         - Pause execution for 2 minutes (120 seconds)
        #         - Add timeout exception handling

        # Return ONLY executable Python code in markdown format.
        # Return ONLY CODE in markdown blocks. No explanations.
        # """
        
        try:
            # response = self.client.chat.completions.create(
            #     model=self.selenium_model,
            #     messages=[{
            #         "role": "system", 
            #         "content": """You are a senior Selenium automation engineer specializing in creating robust, reliable test scripts for Selenium 4.15.2. Generate executable Selenium code using provided selectors. Output ONLY valid Python code in markdown blocks. You write code that:
            #             - Uses best practices for element selection
            #             - Uses the correct WebDriver initialization pattern for Selenium 4.15.2
            #             - Implements proper waits and synchronization
            #             - Handles errors gracefully with retries
            #             - Includes detailed logging and reporting
            #             - Is specific to the website being tested, not generic"""
            #     }, {
            #         "role": "user", 
            #         "content": prompt
            #     }],
            #     temperature=0.2
            # )
            # Extract first Python code block
            #code_block = extract_first_code(response.choices[0].message.content)
            # if not code_block or code_block.language != "python":
            #     raise ValueError("No valid Python code block found")
            
            #return self._extract_code(response.choices[0].message.content)
            #script_content = self._extract_code(response.choices[0].message.content)
            #script_content= response.choices[0].message.content
            # system_prompt = """You are a senior Selenium automation engineer specializing in creating robust, reliable test scripts for Selenium 4.15.2. Generate executable Selenium code using provided selectors. Output ONLY valid Python code in markdown blocks. You write code that:
            #             - Uses best practices for element selection
            #             - Uses the correct WebDriver initialization pattern for Selenium 4.15.2
            #             - Waits for all JavaScript and AJAX on the page to load before starting any test steps
            #             - For CAPTCHA-protected pages:
            #                 - Detect CAPTCHA elements using common selectors
            #                 - Pause execution for manual solving when CAPTCHA is present
            #                 - Add clear console instructions for user intervention
            #             - Implements proper waits and synchronization
            #             - Handles errors gracefully with retries
            #             - Includes detailed logging and reporting
            #             - Is specific to the website being tested, not generic"""

            # system_prompt = self.prompt_manager.get_prompt("generate_script", "system", tool=self.testing_tool)
            system_prompt_template = self.prompt_manager.get_prompt("generate_script", "system", tool=self.testing_tool)
            system_prompt = system_prompt_template.format(selenium_version=self.selenium_version, language=self.language)
            ## For Puppeteer-2.0.0:
            # system_prompt = system_prompt_template.format(language=self.language)
            self.logger.debug(f"system prompt for script generation: {system_prompt}")
            user_prompt_template = self.prompt_manager.get_prompt("generate_script", "user", tool=self.testing_tool)
            # user_prompt = self.prompt_manager.get_prompt("generate_script", "user").format(
            #     test_case=json.dumps(test_case, indent=2),
            #     page_metadata=json.dumps(page_metadata, indent=2),
            #     page_source=page_source,
            #     security_indicators=page_metadata.get('security_indicators', [])
            # )
            # Format with dynamic values
            user_prompt = user_prompt_template.format(
                language=self.language,
                selenium_version=self.selenium_version,
                test_case=json.dumps(test_case, indent=2),
                page_metadata=json.dumps(page_metadata, indent=2),
                page_source=page_source,
                captcha_wait_time=captcha_wait_time,
                security_indicators=page_metadata.get('security_indicators', [])
            )
            script_content= self.llm.generate(system_prompt, user_prompt, model_type="selenium")
            self.logger.debug(f"Raw LLM response generated code: {script_content}")
            # Extract just the Python code if it's wrapped in markdown code blocks
            if "```python" in script_content:
                code = script_content.split("```python")[1].split("```")[0].strip()
            elif "```java" in script_content:
                code = script_content.split("```java")[1].split("```")[0].strip()
            elif "```" in script_content:
                code = script_content.split("```")[1].strip()
            else:
                code = script_content.strip()
            # Save script to file
            if code:
                # Validate script contains required components
                # required_patterns = [
                #     r"from selenium\.webdriver\.common\.by import By",
                #     r"driver\.(find_element|wait)",
                #     r"assert"
                # ]
                # if not all(re.search(pattern, script_content) for pattern in required_patterns):
                #     raise ValueError("Invalid script structure")
                # required_patterns = [
                #     r'from\s+selenium\s+import',
                #     r'webdriver\.Chrome',
                #     r'find_element\(By\.'
                # ]
                # if not all(re.search(p, script_content) for p in required_patterns):
                #     raise ValueError("Invalid Selenium script structure")
                
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
    
    def track_navigation(self, base_url):
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

    # def execute_test_cycle(self, analysis):
    #     for script in analysis['scripts']:
    #         result = self.execute_test_script(script)
    #         self._log_test_result(result)
    #         if not result['success']:
    #             self._handle_test_failure(result, analysis['metadata'])

    def execute_test_cycle(self, analysis):
        for script in analysis['scripts']:
            if not self.validate_script_structure(script):
                continue
                
            result = self.execute_test_script(script)
            self._log_test_result(result)

    def validate_script_structure(self, script):
        required_imports = ['from selenium import webdriver', 'By']
        return all(imp in script for imp in required_imports)

    def _execute_auth_test(self, script, test_data):
        try:
            # Dynamically insert test data
            formatted_script = script.format(
                valid_user=test_data['credentials']['valid']['username'],
                invalid_pass=test_data['credentials']['invalid']['password']
            )
            return self._run_script(formatted_script)
        except KeyError as e:
            self.logger.error(f"Missing test data: {str(e)}")
            return {"success": False, "error": "Missing test data"}

    def execute_test_script(self, script):
        try:
            # Validate script content
            if not script.strip():
                return {'success': False, 'error': 'Empty test script'}
                
            # Create temporary file for execution
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
                f.write(script)
                temp_file = f.name
                
            # Execute using subprocess
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
            if os.path.exists(temp_file):
                os.remove(temp_file)

        
    def _log_test_result(self, result):
        self.test_results.append({
            'timestamp': datetime.now().isoformat(),
            'url': self.driver.current_url,
            'result': result
        })

    def _handle_test_failure(self, result, metadata):
        self.logger.error(f"Test failed: {result.get('error', 'Unknown error')}")
        screenshot = self.capture_screenshot()
        self.logger.info(f"Screenshot captured: {screenshot[:50]}...")
        self.logger.debug(f"Page metadata at failure: {json.dumps(metadata)}")

    def generate_report(self):
        report = {
            'start_time': datetime.now().isoformat(),
            'pages_visited': list(self.visited_pages),
            'test_results': self.test_results,
            'success_rate': len([r for r in self.test_results if r['result']['success']]) / len(self.test_results) if self.test_results else 0,
            'generated_scripts': [f for f in os.listdir('test_scripts') if f.endswith('.py')]
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"reports/test_report_{timestamp}.json"
        
        if not os.path.exists('reports'):
            os.makedirs('reports')
            
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report_file

    def _requires_login(self):
        """Use LLM to check if login/registration is required"""
        try:
            #page_html = self.driver.page_source[:5000]
            page_html = self.driver.page_source
            prompt = f"""Analyze this HTML page and respond ONLY with JSON: 
            {{ "requires_auth": boolean }} 
            Does this page contain login/registration forms or auth requirements?
            Page URL: {self.driver.current_url}
            Partial HTML: {page_html}"""

            # response = self.client.chat.completions.create(
            #     model=self.model,
            #     messages=[{
            #         "role": "system",
            #         "content": "You are an authentication detector. Return JSON with 'requires_auth' boolean."
            #     }, {
            #         "role": "user", 
            #         "content": prompt
            #     }],
            #     temperature=0.1,
            #     response_format={"type": "json_object"}
            # )
            #system_prompt = "You are an authentication detector. Return JSON with 'requires_auth' boolean."
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
        
    ## <--- This version of run_workflow function analyzes one single page at a time --->
    def run_workflow(self, url, username=None, password=None):
        self.driver.get(url)
        
        # if self._requires_login():
        #     if not username or not password:
        #         raise ValueError("Login required but credentials not provided")
        #     self.login_to_website(url, username, password)
        
        initial_analysis = self.analyze_page(context=url)
        self.execute_test_cycle(initial_analysis)
        self.track_navigation(url)
        
        self.driver.quit()
        return self.generate_report()


    ## <--- Uncomment this version of run_workflow function to perform recursive url extraction and integrated testing --->
    # def run_workflow(self, base_url, username=None, password=None):
    #     """Enhanced workflow with recursive URL discovery"""
    #     try:
    #         # Extract URLs first
    #         # Extract URLs with 2-level recursion
    #         all_urls = self.url_extractor.extract_urls(base_url, max_depth=1)
    #         if not all_urls:
    #             self.logger.warning("No URLs found to test")
    #             return self.generate_report()

    #         # Process each URL
    #         for url in all_urls:
    #             self.process_single_url(url, username, password)
                
    #         return self.generate_report()
            
    #     finally:
    #         self.driver.quit()

    # def process_single_url(self, url, username, password):
    #     """Process individual URL with existing workflow"""
    #     self.logger.info(f"\n{'='*50}")
    #     self.logger.info(f"Processing URL: {url}")
        
    #     self.driver.get(url)
        
    #     # if self._requires_login():
    #     #     if not username or not password:
    #     #         raise ValueError("Login required but credentials not provided")
    #     #     self.login_to_website(url, username, password)
            
    #     #analysis = self.analyze_page(url)
    #     analysis = self.analyze_page(context=url)
    #     self.execute_test_cycle(analysis)
    #     self.track_navigation(url)

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
            prompt = f"""Extract auth form selectors as JSON:
            {{
                "username_selector": "css_selector", 
                "password_selector": "css_selector",
                "submit_selector": "css_selector",
                "auth_type": "login|registration",
                "additional_fields": {{
                    "field_name": {{
                        "selector": "css_selector",
                        "type": "text|email|tel|date"
                    }}
                }}
            }}
            Current page HTML: {page_html}"""

            # response = self.client.chat.completions.create(
            #     model=self.model,
            #     messages=[{
            #         "role": "system",
            #         "content": "You are a web form analyzer. Return JSON with auth form selectors and field types."
            #     }, {
            #         "role": "user", 
            #         "content": prompt
            #     }],
            #     temperature=0.1,
            #     response_format={"type": "json_object"}
            # )
            #system_prompt= "You are a web form analyzer. Return JSON with auth form selectors and field types."
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

from urllib.parse import urlparse, urljoin

class URLExtractor:
    def __init__(self, driver, logger=None):
        self.driver = driver
        self.logger = logger or logging.getLogger(__name__)
        
    def extract_urls(self, base_url, max_depth=2):
        """Recursively extract unique internal URLs with BFS up to max_depth"""
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
                            #clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}".rstrip('/')
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
        

# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description="Automated Website Testing Agent")
#     parser.add_argument("--url", required=True, help="Website URL to test")
#     parser.add_argument("--username", help="Login username")
#     parser.add_argument("--password", help="Login password")
#     parser.add_argument("--loglevel", "-l", 
#                         default="INFO",
#                         choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
#                         help="Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
#     args = parser.parse_args()

#     tester = WebTestGenerator(log_level=args.loglevel)
#     report_file = tester.run_workflow(args.url, args.username, args.password)
#     print(f"Test report generated: {report_file}")

# Main execution
if __name__ == "__main__":
    # Initialize the generator
    generator = WebTestGenerator(log_level="INFO")
    
    # Generate scripts for each test case
    for test_case in test_cases:
        script = generator.generate_script_for_test_case(test_case, page_metadata, page_source)
        print(f"Generated script for '{test_case['name']}':\n{script}\n")