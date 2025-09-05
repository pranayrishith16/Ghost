from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class MonitorInterface(ABC):
    """Abstract interface for monitoring and experiment tracking"""

    @abstractmethod
    def start_run(self, run_name: str = None, tags: Dict[str, str] = None):
        """Start a new monitoring run"""
        pass

    @abstractmethod
    def log_params(self, params: Dict[str, Any]):
        """Log parameters"""
        pass

    @abstractmethod
    def log_metrics(self, metrics: Dict[str, float], step: int = None):
        """Log metrics"""
        pass

    @abstractmethod
    def log_artifact(self, artifact_path: str, artifact_name: str = None):
        """Log artifacts (files, models, etc.)"""
        pass

    @abstractmethod
    def end_run(self):
        """End current run"""
        pass

    @abstractmethod
    def get_experiment_info(self) -> Dict[str, Any]:
        """Get current experiment information"""
        pass