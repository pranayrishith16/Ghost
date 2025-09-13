from typing import Dict, Any, Optional, List
from zenml.client import Client
from zenml.steps import BaseStep
from zenml.logger import get_logger
from src.interfaces.monitor import MonitorInterface

class ZenMLMonitor(MonitorInterface):
    def __init__(self, experiment_name: str, tracking_uri: Optional[str] = None):
        self.logger = get_logger(__name__)
        self.experiment_name = experiment_name
        # Optionally set ZenML tracking server URI
        if tracking_uri:
            Client().set_tracking_uri(tracking_uri)
        
        self.client = Client()
        self.experiment = self._get_or_create_experiment(experiment_name)
        self.current_run = None
        self.run_id = None

    def _get_or_create_experiment(self, experiment_name: str):
        experiment = self.client.get_experiment(name=experiment_name)
        if not experiment:
            experiment = self.client.create_experiment(name=experiment_name)
            self.logger.info(f"Created ZenML experiment: {experiment_name}")
        else:
            self.logger.info(f"Using existing ZenML experiment: {experiment_name}")
        return experiment

    def start_run(self, run_name: str, params: Optional[Dict[str, Any]] = None) -> str:
        self.current_run = self.client.create_run(
            experiment_name=self.experiment_name,
            run_name=run_name,
            labels=params or {}
        )
        self.run_id = self.current_run.id
        self.logger.info(f"Started ZenML run '{run_name}' with ID: {self.run_id}")

        # Log initial parameters if provided
        if params:
            self.log_params(params)

        return self.run_id

    def end_run(self, run_id: str) -> None:
        # ZenML Python Client does not require explicit run closing,
        # but we can finalize here if needed.
        self.logger.info(f"Ending ZenML run ID: {run_id}")
        self.run_id = None
        self.current_run = None

    def log_params(self, params: Dict[str, Any]) -> None:
        if not self.current_run:
            self.logger.warning("No active ZenML run for logging parameters")
            return
        for key, value in params.items():
            self.current_run.log_parameter(key=str(key), value=str(value))
        self.logger.info(f"Logged parameters: {list(params.keys())}")

    def log_metrics(self, metrics: Dict[str, Any], step: Optional[int] = None) -> None:
        if not self.current_run:
            self.logger.warning("No active ZenML run for logging metrics")
            return
        for key, value in metrics.items():
            if step is not None:
                self.current_run.log_metric(key=str(key), value=float(value), step=step)
            else:
                self.current_run.log_metric(key=str(key), value=float(value))
        self.logger.info(f"Logged metrics: {list(metrics.keys())}")

    def log_artifact(self, artifact_file: str, artifact_name: Optional[str] = None) -> None:
        if not self.current_run:
            self.logger.warning("No active ZenML run for logging artifact")
            return
        name = artifact_name or artifact_file
        self.current_run.log_artifact(artifact_file, artifact_name=name)
        self.logger.info(f"Logged artifact '{name}' from {artifact_file}")

    def log_text(self, text: str, name: str, step: Optional[int] = None) -> None:
        # ZenML does not have a direct "log_text" method, so write to a temp file or string artifact
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".txt") as tmp:
            tmp.write(text)
            tmp_path = tmp.name
        
        try:
            self.log_artifact(tmp_path, artifact_name=name)
            self.logger.info(f"Logged text artifact '{name}'")
        finally:
            os.remove(tmp_path)

    def log_table(self, data: List[Dict[str, Any]], name: str) -> None:
        # Log table as CSV artifact
        import csv
        import tempfile
        import os

        if not data:
            self.logger.warning("No data provided for logging table")
            return

        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8", suffix=".csv") as tmp:
            writer = csv.DictWriter(tmp, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            tmp_path = tmp.name
        
        try:
            self.log_artifact(tmp_path, artifact_name=name)
            self.logger.info(f"Logged table artifact '{name}'")
        finally:
            os.remove(tmp_path)

    def get_run_info(self, run_id: str) -> Dict[str, Any]:
        run = self.client.get_run(run_id)
        if not run:
            self.logger.warning(f"No ZenML run found with id {run_id}")
            return {}
        info = {
            "run_id": run.id,
            "name": run.name,
            "status": run.status,
            "start_time": run.created,
            "end_time": run.finished,
        }
        return info

    def log_tags(self, tags: Dict[str, str]) -> None:
        if not self.current_run:
            self.logger.warning("No active ZenML run for logging tags")
            return
        for key, value in tags.items():
            self.current_run.set_label(key, value)
        self.logger.info(f"Logged tags: {list(tags.keys())}")

    def __enter__(self):
        # Context manager entry
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Context manager exit
        if self.run_id:
            self.end_run(self.run_id)