import json
import re
from datetime import datetime
from bs4 import BeautifulSoup, Comment
from app.config.database import SessionLocal
from shared_orm.models.page import Page


class PageAnalysisService:

    def __init__(self, driver, logger, llm, prompt_manager):
        self.driver = driver
        self.logger = logger
        self.llm = llm
        self.prompt_manager = prompt_manager

    def analyze_page(self, page_id: int, page_url: str, requested_by: str):
        self.logger.info(f"[PAGE_ANALYSE] Loading {page_url}")

        self.driver.get(page_url)

        page_source = self.driver.page_source
        minimized_html = self.extract_test_relevant_html(page_source) # fetch page source

        static_metadata = {
            "title": self.driver.title,
            "url": self.driver.current_url,
        }

        llm_metadata = self.llm_page_analysis(minimized_html) # fetch page metadata

        page_metadata = {
            **static_metadata,
            **llm_metadata
        }

        with SessionLocal() as db:
            page = db.query(Page).filter(Page.id == page_id).first()

            page.page_title = self.driver.title
            page.page_source = minimized_html
            page.page_metadata = page_metadata
            page.status = "processed"
            page.updated_on = datetime.utcnow()
            page.updated_by = requested_by

            db.commit()

    def extract_test_relevant_html(self, page_source):
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
