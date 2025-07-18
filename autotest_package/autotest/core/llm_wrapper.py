"""
LLM Wrapper module for handling different language model providers
"""
import os
import yaml
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage


class LLMWrapper:
    """Wrapper class for handling different LLM providers"""
    
    def __init__(self, config_path=None):
        """
        Initialize LLM wrapper with configuration
        
        Args:
            config_path (str, optional): Path to configuration file
        """
        if config_path is None:
            # Get the package directory and default config path
            package_dir = os.path.dirname(os.path.dirname(__file__))
            config_path = os.path.join(package_dir, '..', 'config', 'llm_config.yaml')
            
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
            
        self.provider = self.config["model_provider"]
        self.models = self._initialize_models()

    def _initialize_models(self):
        """Initialize model instances based on provider configuration"""
        provider = self.config["model_provider"]
        params = self.config["model_settings"].get(provider, {})

        # Get API key based on provider
        api_key = os.getenv(
            "OPENAI_API_KEY" if provider == "openai" else "GROQ_API_KEY"
        )

        if provider == "openai":
            return {
                "analysis": ChatOpenAI(
                    api_key=api_key, 
                    model=params["analysis_model"], 
                    temperature=params["temperature"], 
                    model_kwargs={"response_format": {"type": "json_object"}}
                ),
                "selenium": ChatOpenAI(
                    api_key=api_key, 
                    model=params["selenium_model"], 
                    temperature=params["temperature"]
                )
            }
        elif provider == "groq":
            return {
                "analysis": ChatGroq(
                    api_key=api_key, 
                    model=params["analysis_model"], 
                    temperature=params["temperature"], 
                    model_kwargs={"response_format": {"type": "json_object"}}
                ),
                "selenium": ChatGroq(
                    api_key=api_key, 
                    model=params["selenium_model"], 
                    temperature=params["temperature"]
                )
            }
        elif provider == "google-gemini":
            return {
                "analysis": ChatGoogleGenerativeAI(
                    api_key=os.getenv("GOOGLE_API_KEY"), 
                    model=params["analysis_model"], 
                    temperature=params["temperature"], 
                    model_kwargs={"response_format": {"type": "json_object"}}
                ),
                "selenium": ChatGoogleGenerativeAI(
                    api_key=os.getenv("GOOGLE_API_KEY"), 
                    model=params["selenium_model"], 
                    temperature=params["temperature"]
                )
            }
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def generate(self, system_prompt, user_prompt, model_type="analysis"):
        """
        Generate response using specified model type
        
        Args:
            system_prompt (str): System prompt for the model
            user_prompt (str): User prompt for the model
            model_type (str): Type of model to use ('analysis' or 'selenium')
            
        Returns:
            str: Generated response content
        """
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        return self.models[model_type].invoke(messages).content
    
    def get_provider(self):
        """Get current provider name"""
        return self.provider
    
    def get_available_models(self):
        """Get list of available model types"""
        return list(self.models.keys())