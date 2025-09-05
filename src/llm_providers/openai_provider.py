import logging
from typing import Dict, Any, Optional, List
import openai
from openai import OpenAI

from archive_src.interfaces.llm_provider import LLMProviderInterface
from archive_src.config.settings import get_config
from archive_src.core.exceptions import LLMGenerationError, LLMConnectionError

class OpenAIProvider(LLMProviderInterface):
    """OpenAI LLM provider implementation"""
    
    def __init__(self):
        self.config = get_config().llm
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url or "https://api.openai.com/v1"
        )
        
        self.model_info = {
            'provider': 'openai',
            'model_name': self.config.model_name,
            'max_tokens': self.config.max_tokens,
            'temperature': self.config.temperature
        }
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None, 
                temperature: Optional[float] = None) -> str:
        """Generate text from prompt using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": self.config.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                top_p=self.config.top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty
            )
            
            return response.choices[0].message.content
            
        except openai.APIConnectionError as e:
            self.logger.error(f"OpenAI connection error: {e}")
            raise LLMConnectionError(f"OpenAI connection failed: {e}")
        except openai.APIError as e:
            self.logger.error(f"OpenAI API error: {e}")
            raise LLMGenerationError(f"OpenAI API error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in OpenAI generation: {e}")
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
        
        return self.generate(prompt, max_tokens, temperature=0.1)  # Low temp for factual responses
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return self.model_info
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using simple approximation"""
        # For more accurate tokenization, consider using tiktoken
        return len(text.split()) * 1.3  # Rough approximation
    
    def validate_response(self, response: str) -> bool:
        """Validate generated response meets quality criteria"""
        if not response or response.strip() == "":
            return False
        
        # Check for common error patterns
        error_patterns = [
            "I'm sorry", "I cannot", "as an AI", "I don't have",
            "I am not able", "I do not have", "I'm not able"
        ]
        
        response_lower = response.lower()
        if any(pattern in response_lower for pattern in error_patterns):
            return False
            
        # Minimum length check
        if len(response.split()) < 5:  # At least 5 words
            return False
            
        return True