from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class LLMProviderInterface(ABC):
    """Abstract interface for LLM providers"""

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int = None, temperature: float = None) -> str:
        """Generate text from prompt"""
        pass

    @abstractmethod
    def generate_with_context(self, question: str, context: List[str], max_tokens: int = None) -> str:
        """Generate answer using provided context"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        pass

    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count"""
        pass

    @abstractmethod
    def validate_response(self, response: str) -> bool:
        """Validate generated response"""
        pass