from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .llm_provider_interface import LLMProviderInterface

class LegalLLMInterface(LLMProviderInterface):
    """Legal-specific LLM interface extending base LLM interface"""
    
    @abstractmethod
    def generate_legal_summary(self, case_text: str, summary_type: str = "brief", **kwargs) -> str:
        """Generate legal document summary"""
        pass
        
    @abstractmethod
    def analyze_legal_precedents(self, question: str, cases: List[str], **kwargs) -> str:
        """Analyze legal precedents for a question"""
        pass
        
    @abstractmethod
    def extract_legal_entities(self, text: str, **kwargs) -> Dict[str, List[str]]:
        """Extract legal entities from text"""
        pass
