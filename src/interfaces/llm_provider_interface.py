"""Abstract interface for Large Language Model providers"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum

class FinishReason(Enum):
    COMPLETED = "completed"
    MAX_TOKENS = "max_tokens"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"

@dataclass
class GenerationConfig:
    """Configuration for text generation"""
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    stream: bool = False
    return_full_result: bool = False

@dataclass
class GenerationResult:
    """Result from text generation"""
    text: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None
    model_used: Optional[str] = None
    cost_estimate: Optional[float] = None
    latency_ms: Optional[float] = None

class LLMProviderInterface(ABC):
    """Abstract interface for LLM providers"""
    
    @abstractmethod
    def generate(self, 
                 prompt: str, 
                 config: Optional[GenerationConfig] = None,
                 **kwargs) -> Union[str, GenerationResult]:
        """
        Generate text from prompt
        
        Args:
            prompt: Input prompt for generation
            config: Generation configuration
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text or detailed result
        """
        pass
    
    @abstractmethod
    def generate_with_context(self, 
                            question: str, 
                            context: List[str], 
                            config: Optional[GenerationConfig] = None,
                            **kwargs) -> Union[str, GenerationResult]:
        """
        Generate answer using provided context (RAG)
        
        Args:
            question: User's question
            context: List of relevant context chunks
            config: Generation configuration
            **kwargs: Additional parameters
            
        Returns:
            Generated answer or detailed result
        """
        pass
    
    @abstractmethod
    def generate_streaming(self, 
                          prompt: str, 
                          config: Optional[GenerationConfig] = None,
                          **kwargs):
        """
        Generate text with streaming response
        
        Args:
            prompt: Input prompt
            config: Generation configuration
            **kwargs: Additional parameters
            
        Yields:
            Incremental text chunks
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information and capabilities
        
        Returns:
            Dictionary containing model metadata
        """
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for given text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Estimated number of tokens
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, 
                     input_tokens: int, 
                     output_tokens: int) -> float:
        """
        Estimate cost for given token usage
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        pass
    
    @abstractmethod
    def validate_response(self, response: str) -> bool:
        """
        Validate generated response quality
        
        Args:
            response: Generated text to validate
            
        Returns:
            True if response is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def check_content_policy(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check if text violates content policies
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (is_safe, reason_if_unsafe)
        """
        pass
    
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get current rate limit information"""
        return {
            'requests_per_minute': None,
            'tokens_per_minute': None,
            'requests_per_day': None
        }