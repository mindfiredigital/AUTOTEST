"""
LLM Wrapper module for handling different language model providers
"""
import os
import yaml
from shared_orm.utils.encryption import decrypt_value
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage
from shared_orm.models.provider import Provider


class LLMWrapper:
    """Wrapper class for handling different LLM providers"""
    
    def __init__(self, db, config_path=None):
        """
        Initialize LLM wrapper with configuration.

        Args:
            db: SQLAlchemy session used only during __init__ to fetch the active
                provider. The reference is NOT retained after initialization.
            config_path (str, optional): Path to configuration file
        """
        if config_path is None:
            # Get the package directory and default config path
            package_dir = os.path.dirname(os.path.dirname(__file__))
            config_path = os.path.join(package_dir, 'config', 'llm_config.yaml')

        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        provider_data = self._get_active_provider_from_db(db)

        self.provider = self._map_provider_name(provider_data.title)
        self.api_key = decrypt_value(provider_data.key)

        if not self.provider:
            raise ValueError(f"Unsupported provider: {provider_data.title}")
        if self.provider != "ollama" and not self.api_key:
            raise ValueError(f"API key missing for provider: {provider_data.title}")
        
        self.models = self._initialize_models()

    
    def _get_active_provider_from_db(self, db):
        provider = (
            db.query(Provider)
            .filter(Provider.is_active == True)
            .first()
        )
        if not provider:
            raise ValueError("No active LLM provider found in DB")
        return provider
    
    def _map_provider_name(self, db_name):
        mapping = {
            "OpenAI": "openai",
            "Gemini": "google-gemini",
            "Claude": "anthropic",
            "Ollama": "ollama"
        }
        return mapping.get(db_name)
    

    def _initialize_models(self):
        """Initialize model instances based on provider configuration"""
        # provider = self.config["model_provider"]
        provider = self.provider
        # params = self.config["model_settings"].get(provider, {})
        params = self.config["providers"].get(provider, {})  # Changed from model_settings to providers
        if not params:
            raise ValueError(f"Configuration not found for provider: {provider}")

        # Get API key based on provider
        # api_key = os.getenv(
        #     "OPENAI_API_KEY" if provider == "openai" else "GROQ_API_KEY"
        # )

        # api_key = os.getenv(
        #     "OPENAI_API_KEY" if provider == "openai" else 
        #     "GROQ_API_KEY" if provider == "groq" else
        #     "GOOGLE_API_KEY" if provider == "google-gemini" else
        #     "ANTHROPIC_API_KEY"
        # )

        api_key = self.api_key

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
                ),
                "result_analysis": ChatOpenAI(
                    api_key=api_key, 
                    model=params["result_analysis_model"], 
                    temperature=1.0, 
                    model_kwargs={"response_format": {"type": "json_object"}}
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
                ),
                "result_analysis": ChatGroq(
                    api_key=api_key, 
                    model=params["result_analysis_model"], 
                    temperature=params["temperature"], 
                    model_kwargs={"response_format": {"type": "json_object"}}
                )
            }
        elif provider == "google-gemini":
            return {
                "analysis": ChatGoogleGenerativeAI(
                    # api_key=os.getenv("GOOGLE_API_KEY"), 
                    api_key=api_key,
                    model=params["analysis_model"], 
                    temperature=params["temperature"], 
                   # model_kwargs={"response_format": {"type": "json_object"}}
                ),
                "selenium": ChatGoogleGenerativeAI(
                    # api_key=os.getenv("GOOGLE_API_KEY"), 
                    api_key=api_key,
                    model=params["selenium_model"], 
                    temperature=params["temperature"]
                ),
                "result_analysis": ChatGoogleGenerativeAI(
                    # api_key=os.getenv("GOOGLE_API_KEY"), 
                    api_key=api_key,
                    model=params["result_analysis_model"], 
                    temperature=params["temperature"], 
                   # model_kwargs={"response_format": {"type": "json_object"}}
                ),
            }
        
        elif provider == "anthropic":
            return {
                "analysis": ChatAnthropic(
                    api_key=api_key,
                    model=params["analysis_model"],
                    temperature=params["temperature"],
                    # model_kwargs={"response_format": {"type": "json_object"}}
                ),
                "selenium": ChatAnthropic(
                    api_key=api_key,
                    model=params["selenium_model"],
                    temperature=params["temperature"]
                ),
                "result_analysis": ChatAnthropic(
                    api_key=api_key,
                    model=params["result_analysis_model"],
                    temperature=params["temperature"],
                    # model_kwargs={"response_format": {"type": "json_object"}}
                ),
            }
        
        elif provider == "ollama":
            return {
                "analysis": ChatOllama(
                    model=params["analysis_model"],
                    temperature=params["temperature"],
                    format="json"  # Native JSON mode for Ollama
                ),
                "selenium": ChatOllama(
                    model=params["selenium_model"],
                    temperature=params["temperature"]
                ),
                "result_analysis": ChatOllama(
                    model=params["result_analysis_model"],
                    temperature=params["temperature"],
                    format="json"  # Native JSON mode for Ollama
                ),
            }
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
    def _needs_json_in_prompt(self):
        """Check if provider needs JSON instruction in prompt instead of model_kwargs"""
        return self.provider in ["google-gemini", "anthropic", "ollama"]

    def generate(self, system_prompt, user_prompt, model_type="analysis"):
        """
        Generate response using specified model type
        
        Args:
            system_prompt (str): System prompt for the model
            user_prompt (str): User prompt for the model
            model_type (str): Type of model to use ('analysis', 'selenium' or 'result_analysis')
            
        Returns:
            str: Generated response content
        """

        # For providers that don't support response_format, add JSON instruction to prompt
        if (model_type == "analysis" or model_type == "result_analysis") and self._needs_json_in_prompt():
            json_instruction = "\n\nIMPORTANT: Please respond with valid JSON format only. Do not include any text outside the JSON structure."
            system_prompt += json_instruction

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        try:
            return self.models[model_type].invoke(messages).content
        except Exception as e:
            raise RuntimeError(f"Error generating response with {self.provider} ({model_type} model): {str(e)}")
    
    def get_provider(self):
        """Get current provider name"""
        return self.provider
    
    def get_available_models(self):
        """Get list of available model types"""
        return list(self.models.keys())
    
    def supports_json_mode(self):
        """Check if current provider supports native JSON mode"""
        return self.provider in ["openai", "groq", "ollama"]
    
    def get_provider_info(self):
        """Get detailed information about current provider"""
        return {
            "provider": self.provider,
            "supports_json_mode": self.supports_json_mode(),
            "needs_json_in_prompt": self._needs_json_in_prompt(),
            "available_models": self.get_available_models(),
            "requires_api_key": self.provider != "ollama"
        }