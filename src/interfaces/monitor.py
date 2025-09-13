from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

class MonitorInterface(ABC):

    @abstractmethod
    def log_metrics(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
        """Log metrics with optional step number"""
        raise NotImplementedError

    @abstractmethod
    def log_artifact(self, artifact_file: str, artifact_name: Optional[str] = None) -> None:
        """Log artifact file"""
        raise NotImplementedError
    
    # Add these new methods:
    @abstractmethod
    def start_run(self, run_name: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Start a new monitoring run, returns run_id"""
        raise NotImplementedError
    
    @abstractmethod
    def get_run_info(self, run_id: str) -> Dict[str, Any]:
        """Retrieve information about a given run"""
        raise NotImplementedError
        
    @abstractmethod
    def end_run(self, run_id: str) -> None:
        """End a monitoring run"""
        raise NotImplementedError
        
    @abstractmethod
    def log_text(self, text: str, name: str, step: Optional[int] = None) -> None:
        """Log text content"""
        raise NotImplementedError
        
    @abstractmethod
    def log_table(self, data: List[Dict[str, Any]], name: str) -> None:
        """Log tabular data"""
        raise NotImplementedError
        
    @contextmanager
    def run_context(self, run_name: str, config: Optional[Dict[str, Any]] = None):
        """Context manager for runs"""
        run_id = self.start_run(run_name, config)
        try:
            yield run_id
        finally:
            self.end_run(run_id)
    
    @abstractmethod
    def log_params(self, params:Dict[str,Any]) -> None:
        """Log hyperparameters or configuration params"""
        raise NotImplementedError