import logging
from typing import Dict, Any, Optional, List
import anthropic

from archive_src.interfaces.llm_provider import LLMProviderInterface
from archive_src.config.settings import get_config
from archive_src.core.exceptions import LLMGenerationError, LLMConnectionError

class AnthropicProvider(LLMProviderInterface):
    """Anthropic Claude LLM provider implementation"""
    
    def __init__(self):
        self.config = get_config().llm
        self.logger = logging.getLogger(__name__)
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(
            api_key=self.config.api_key,
            base_url=self.config.base_url or "https://api.anthropic.com"
        )
        
        self.model_info = {
            'provider': 'anthropic',
            'model_name': self.config.model_name,
            'max_tokens': self.config.max_tokens
        }
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None, 
                temperature: Optional[float] = None) -> str:
        """Generate text from prompt using Anthropic API"""
        try:
            response = self.client.messages.create(
                model=self.config.model_name,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                system=self.config.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except anthropic.APIConnectionError as e:
            self.logger.error(f"Anthropic connection error: {e}")
            raise LLMConnectionError(f"Anthropic connection failed: {e}")
        except anthropic.APIError as e:
            self.logger.error(f"Anthropic API error: {e}")
            raise LLMGenerationError(f"Anthropic API error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in Anthropic generation: {e}")
            raise LLMGenerationError(f"Unexpected error: {e}")
    
    def generate_with_context(self, question: str, context: List[str], 
                            max_tokens: Optional[int] = None) -> str:
        """Generate answer using provided context for RAG"""
        context_text = "\n\n".join(context)
        
        prompt = f"""<context>
{context_text}
</context>

Based strictly on the provided legal context, answer the following question thoroughly and accurately.

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
        
        # Check for refusal patterns specific to Claude
        refusal_patterns = [
            "I apologize", "I cannot", "I'm not able", 
            "I don't have", "based on the information"
        ]
        
        response_lower = response.lower()
        if any(pattern in response_lower for pattern in refusal_patterns):
            return False
            
        if len(response.split()) < 5:
            return False
            
        return True