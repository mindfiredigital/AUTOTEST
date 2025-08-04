"""
LLM Wrapper module for handling different language model providers
"""
import os
import yaml
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
# from langchain_community.chat_models import ChatOllama
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, SystemMessage


class LLMWrapper:
    """Wrapper class for handling different LLM providers"""
    
    def __init__(self, config_path=None, llm_provider_choice=1):
        """
        Initialize LLM wrapper with configuration
        
        Args:
            config_path (str, optional): Path to configuration file
            llm_provider_choice (int): Provider choice (1=OpenAI, 2=Groq, 3=Google-Gemini, 4=Anthropic, 5=Ollama)
        """
        if config_path is None:
            # Get the package directory and default config path
            package_dir = os.path.dirname(os.path.dirname(__file__))
            config_path = os.path.join(package_dir, '..', 'config', 'llm_config.yaml')
            
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # Override provider based on user choice
        provider_mapping = {
            1: "openai",
            2: "groq", 
            3: "google-gemini",
            4: "anthropic",
            5: "ollama"
        }
            
        # self.provider = self.config["model_provider"]
        # self.provider = provider_mapping[llm_provider_choice]
        self.provider = provider_mapping.get(llm_provider_choice)
        if not self.provider:
            raise ValueError(f"Invalid provider choice: {llm_provider_choice}. Valid choices: {list(provider_mapping.keys())}")
        self.models = self._initialize_models()

    def _get_api_key(self, provider):
        """Get API key for the specified provider"""
        if provider == "ollama":
            return None # Ollama does not require an API key
        
        key_mapping = {
            "openai": "OPENAI_API_KEY",
            "groq": "GROQ_API_KEY",
            "google-gemini": "GOOGLE_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY"
        }
        
        api_key = os.getenv(key_mapping[provider])
        if not api_key:
            raise ValueError(f"API key not found for provider: {provider}. Set {key_mapping[provider]} environment variable.")
        
        return api_key

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

        api_key = self._get_api_key(provider)

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
                )
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
                )
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
                )
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
            model_type (str): Type of model to use ('analysis' or 'selenium')
            
        Returns:
            str: Generated response content
        """

        # For providers that don't support response_format, add JSON instruction to prompt
        if model_type == "analysis" and self._needs_json_in_prompt():
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