import logging
import time
from typing import List, Dict, Any, Optional
import tiktoken

from src.interfaces.llm_provider_interface import LLMProviderInterface
from config.settings import get_config

try:
    import openai
except ImportError:
    raise ImportError("Please install openai: pip install openai")

class OpenRouterProvider(LLMProviderInterface):
    """OpenRouter provider for accessing multiple LLM models through unified API"""
    
    def __init__(self):
        self.config = get_config().llm
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenRouter client (uses OpenAI SDK with custom base URL)
        if not self.config.api_key:
            raise Exception("OpenRouter API key is required")
        
        # OpenRouter uses OpenAI-compatible API
        self.client = openai.OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url or "https://openrouter.ai/api/v1"
        )
            
        # Initialize tokenizer for token counting
        try:
            # For OpenRouter, use a generic tokenizer since models vary
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.logger.warning("Could not initialize tokenizer, using fallback estimation")
            self.tokenizer = None
            
        self.logger.info(f"Initialized OpenRouter provider with model: {self.config.model_name}")
    
    def generate(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """Generate text from prompt"""
        try:
            # OpenRouter-specific headers
            extra_headers = {
                "HTTP-Referer": "https://your-app.com",  # Replace with your app URL
                "X-Title": "Law RAG System",  # Your app name
            }
            
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
                presence_penalty=self.config.presence_penalty,
                extra_headers=extra_headers
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"OpenRouter generation failed: {str(e)}")
            raise Exception(f"OpenRouter generation failed: {str(e)}")
    
    def generate_with_context(self, question: str, context: List[str], max_tokens: int = None) -> str:
        """Generate answer using provided context"""
        try:
            # Build context-aware prompt
            context_text = "\n\n".join(context) if isinstance(context, list) else context[0]
            
            # Check token limits
            estimated_tokens = self.estimate_tokens(context_text + question)
            if estimated_tokens > self.config.max_context_length:
                self.logger.warning(f"Context too long ({estimated_tokens} tokens), truncating...")
                context_text = self._truncate_context(context_text, question)
            
            # OpenRouter-specific headers
            extra_headers = {
                "HTTP-Referer": "https://your-app.com",  # Replace with your app URL
                "X-Title": "Law RAG System",  # Your app name
            }
            
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": self.config.system_prompt},
                    {"role": "user", "content": context_text}
                ],
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty,
                extra_headers=extra_headers,
                # OpenRouter specific options
                extra_body={
                    "provider": {
                        "allow_fallbacks": True,  # Enable fallback to other providers
                        "data_collection": "allow"  # or "deny" for privacy
                    }
                }
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"OpenRouter context generation failed: {str(e)}")
            raise Exception(f"OpenRouter context generation failed: {str(e)}")
    
    def generate_with_fallbacks(self, question: str, context: List[str], 
                               preferred_providers: List[str] = None, max_tokens: int = None) -> str:
        """Generate with OpenRouter's provider fallback system"""
        try:
            context_text = "\n\n".join(context) if isinstance(context, list) else context[0]
            
            extra_body = {
                "provider": {
                    "allow_fallbacks": True,
                    "data_collection": "allow"
                }
            }
            
            # Add provider preferences if specified
            if preferred_providers:
                extra_body["provider"]["order"] = preferred_providers
                
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": self.config.system_prompt},
                    {"role": "user", "content": context_text}
                ],
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=self.config.temperature,
                extra_body=extra_body,
                extra_headers={
                    "HTTP-Referer": "https://your-app.com",
                    "X-Title": "Law RAG System",
                }
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"OpenRouter fallback generation failed: {str(e)}")
            raise Exception(f"OpenRouter fallback generation failed: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            'provider': 'openrouter',
            'model_name': self.config.model_name,
            'max_tokens': self.config.max_tokens,
            'temperature': self.config.temperature,
            'max_context_length': self.config.max_context_length,
            'base_url': self.config.base_url or "https://openrouter.ai/api/v1"
        }
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception:
                pass
        
        # Fallback estimation: roughly 4 characters per token
        return len(text) // 4
    
    def validate_response(self, response: str) -> bool:
        """Validate generated response"""
        if not response or len(response.strip()) == 0:
            return False
        
        # Check for common error patterns
        error_patterns = ['error', 'failed', 'unable to process', 'rate limit', 'insufficient credits']
        response_lower = response.lower()
        
        return not any(pattern in response_lower for pattern in error_patterns)
    
    def _truncate_context(self, context: str, question: str) -> str:
        """Truncate context to fit within token limits"""
        question_tokens = self.estimate_tokens(question)
        max_context_tokens = self.config.max_context_length - question_tokens - 100  # Safety margin
        
        if max_context_tokens <= 0:
            return context[:1000]  # Minimal context
        
        # Rough character estimation
        max_chars = max_context_tokens * 4
        if len(context) <= max_chars:
            return context
            
        return context[:max_chars] + "\n...[Context truncated]"
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from OpenRouter"""
        try:
            # This would require a separate request to OpenRouter's models endpoint
            # For now, return basic info
            return [{
                'id': self.config.model_name,
                'provider': 'openrouter',
                'context_length': self.config.max_context_length
            }]
        except Exception as e:
            self.logger.error(f"Failed to get available models: {str(e)}")
            return []
        
    def generate_streaming(self, prompt, config = None, **kwargs):
        return
    
    def estimate_cost(self, input_tokens, output_tokens):
        return
    
    def check_content_policy(self, text):
        return