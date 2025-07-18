"""
Prompt Manager module for handling prompt templates
"""
import os
import yaml


class PromptManager:
    """Manager class for handling prompt templates from YAML configuration"""
    
    def __init__(self, prompt_file=None):
        """
        Initialize prompt manager with prompt file
        
        Args:
            prompt_file (str, optional): Path to prompts YAML file
        """
        if prompt_file is None:
            # Get the package directory and default prompt file path
            package_dir = os.path.dirname(os.path.dirname(__file__))
            prompt_file = os.path.join(package_dir, 'config', 'prompts4.yaml')
            
        with open(prompt_file, "r", encoding="utf-8") as f:
            self.prompts = yaml.safe_load(f)

    def get_prompt(self, section, role, tool=None):
        """
        Get prompt template from configuration
        
        Args:
            section (str): Section name (e.g., 'llm_page_analysis')
            role (str): Role ('system' or 'user')
            tool (str, optional): Tool name for tool-specific prompts
            
        Returns:
            str: Prompt template string
        """
        if tool and section == "generate_script":
            return self.prompts[section][tool][role]
        return self.prompts[section][role]
    
    def get_available_sections(self):
        """Get list of available prompt sections"""
        return list(self.prompts.keys())
    
    def get_section_roles(self, section):
        """Get available roles for a specific section"""
        if section in self.prompts:
            return list(self.prompts[section].keys())
        return []
    
    def get_section_tools(self, section):
        """Get available tools for a specific section"""
        if section in self.prompts and isinstance(self.prompts[section], dict):
            # Check if any values are dictionaries (indicating tool-specific prompts)
            tools = []
            for key, value in self.prompts[section].items():
                if isinstance(value, dict) and 'system' in value:
                    tools.append(key)
            return tools
        return []