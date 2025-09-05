import logging
from typing import Dict, Any, Optional, List
import requests

from src.interfaces.llm_provider import LLMProviderInterface
from src.config.settings import get_config
from src.core.exceptions import LLMGenerationError, LLMConnectionError

class LocalProvider(LLMProviderInterface):
    """Local LLM provider implementation (Ollama, LocalAI, etc.)"""
    
    def __init__(self):
        self.config = get_config().llm
        self.logger = logging.getLogger(__name__)
        
        self.model_info = {
            'provider': 'local',
            'model_name': self.config.model_name,
            'base_url': self.config.base_url
        }
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None, 
                temperature: Optional[float] = None) -> str:
        """Generate text using local LLM API"""
        try:
            # Prepare the request for Ollama/LocalAI compatible API
            payload = {
                "model": self.config.model_name,
                "prompt": f"{self.config.system_prompt}\n\n{prompt}",
                "stream": False,
                "options": {
                    "temperature": temperature or self.config.temperature,
                    "top_p": self.config.top_p,
                    "num_predict": max_tokens or self.config.max_tokens
                }
            }
            
            response = requests.post(
                f"{self.config.base_url}/api/generate",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code != 200:
                raise LLMConnectionError(f"API request failed: {response.text}")
            
            result = response.json()
            return result.get('response', '').strip()
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Local LLM connection error: {e}")
            raise LLMConnectionError(f"Local LLM connection failed: {e}")
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Local LLM timeout: {e}")
            raise LLMConnectionError(f"Local LLM timeout: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in local generation: {e}")
            raise LLMGenerationError(f"Unexpected error: {e}")
    
    def generate_with_context(self, question: str, context: List[str], 
                            max_tokens: Optional[int] = None) -> str:
        """Generate answer using provided context for RAG"""
        context_text = "\n\n".join(context)
        
        prompt = f"""Based on the following legal context, answer the question thoroughly and accurately.

Context:
{context_text}

Question: {question}

Answer:"""
        
        return self.generate(prompt, max_tokens, temperature=0.1)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return self.model_info
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count"""
        return len(text.split()) * 1.3  # Rough approximation
    
    def validate_response(self, response: str) -> bool:
        """Validate generated response"""
        if not response or response.strip() == "":
            return False
            
        # Check for empty or very short responses
        if len(response.split()) < 5:
            return False
            
        return True