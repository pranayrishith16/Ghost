import logging
from typing import Dict, Any, Optional, List
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

from src.interfaces.llm_provider import LLMProviderInterface
from src.config.settings import get_config
from src.core.exceptions import LLMGenerationError

class HuggingFaceProvider(LLMProviderInterface):
    """HuggingFace Transformers LLM provider implementation"""
    
    def __init__(self):
        self.config = get_config().llm
        self.logger = logging.getLogger(__name__)
        
        # Load model and tokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name,
                trust_remote_code=self.config.trust_remote_code
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                torch_dtype=torch.float16 if self.config.device == "cuda" else torch.float32,
                device_map="auto" if self.config.device == "cuda" else None,
                trust_remote_code=self.config.trust_remote_code
            )
            
            # Create text generation pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.config.device == "cuda" else -1
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load HuggingFace model: {e}")
            raise LLMGenerationError(f"Model loading failed: {e}")
        
        self.model_info = {
            'provider': 'huggingface',
            'model_name': self.config.model_name,
            'device': self.config.device
        }
    
    def generate(self, prompt: str, max_tokens: Optional[int] = None, 
                temperature: Optional[float] = None) -> str:
        """Generate text using local HuggingFace model"""
        try:
            # Prepare the prompt with system message
            full_prompt = f"{self.config.system_prompt}\n\nUser: {prompt}\n\nAssistant:"
            
            # Generate response
            outputs = self.generator(
                full_prompt,
                max_new_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                top_p=self.config.top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract the generated text
            generated_text = outputs[0]['generated_text']
            
            # Remove the input prompt to get only the response
            response = generated_text.replace(full_prompt, "").strip()
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in HuggingFace generation: {e}")
            raise LLMGenerationError(f"Generation failed: {e}")
    
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
        """Estimate token count using the model's tokenizer"""
        if hasattr(self, 'tokenizer'):
            return len(self.tokenizer.encode(text))
        return len(text.split()) * 1.3  # Fallback approximation
    
    def validate_response(self, response: str) -> bool:
        """Validate generated response"""
        if not response or response.strip() == "":
            return False
            
        # Check for repetition or gibberish (simple check)
        words = response.split()
        if len(set(words)) / len(words) < 0.5:  # High repetition
            return False
            
        if len(words) < 5:
            return False
            
        return True