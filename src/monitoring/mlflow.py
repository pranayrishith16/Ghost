from typing import Dict, Any, Optional, List
import mlflow
import tempfile
import os
import csv
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient
from src.interfaces.monitor import MonitorInterface
import logging

class MLFlowMonitor(MonitorInterface):
    def __init__(self, experiment_name: str, tracking_uri: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient()
        try:
            self.experiment_id = self.client.create_experiment(experiment_name)
            self.logger.info(f"Created new MLflow experiment: {experiment_name} (id={self.experiment_id})")
        except MlflowException:
            self.experiment_id = self.client.get_experiment_by_name(experiment_name).experiment_id
            self.logger.info(f"Using existing MLflow experiment: {experiment_name} (id={self.experiment_id})")
        self.run = None
        self.run_id = None

    def start(self, run_name: str, params: Optional[Dict[str, Any]] = None):
        self.run = mlflow.start_run(experiment_id=self.experiment_id, run_name=run_name)
        self.run_id = self.run.info.run_id
        self.logger.info(f"Started MLflow run '{run_name}' with id {self.run_id}")
        if params:
            self.log_params(params)
        return self.run_id

    def start_run(self, run_name: str, params: Optional[Dict[str, Any]] = None) -> str:
        return self.start(run_name, params)

    def end_run(self, run_id: str):
        mlflow.end_run()
        self.logger.info(f"Ended MLflow run {run_id}")
        self.run = None
        self.run_id = None

    def log_params(self, params: Dict[str, Any]):
        if not self.run:
            self.logger.warning("No active MLflow run to log parameters")
            return
        mlflow.log_params(params)
        self.logger.info(f"Logged MLflow parameters: {list(params.keys())}")

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        if not self.run:
            self.logger.warning("No active MLflow run to log metrics")
            return
        for key, value in metrics.items():
            if step is not None:
                mlflow.log_metric(key, value, step)
            else:
                mlflow.log_metric(key, value)
        self.logger.info(f"Logged MLflow metrics: {list(metrics.keys())}")

    def log_artifact(self, artifact_path: str, artifact_name: Optional[str] = None):
        if not self.run:
            self.logger.warning("No active MLflow run to log artifact")
            return
        mlflow.log_artifact(artifact_path, artifact_path if artifact_name is None else artifact_name)
        self.logger.info(f"Logged MLflow artifact: {artifact_path}")

    def log_text(self, text: str, name: str, step: Optional[int] = None):
        # Write text to a temporary file and log as artifact
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as f:
            f.write(text)
            temp_path = f.name
        try:
            self.log_artifact(temp_path, name)
        finally:
            os.remove(temp_path)
        self.logger.info(f"Logged MLflow text as artifact: {name}")

    def log_table(self, data: List[Dict[str, Any]], name: str):
        if not data:
            self.logger.warning("No data to log in MLflow table")
            return
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            temp_path = f.name
        try:
            self.log_artifact(temp_path, name)
        finally:
            os.remove(temp_path)
        self.logger.info(f"Logged MLflow table as artifact: {name}")

    def get_run_info(self, run_id: str) -> Dict[str, Any]:
        try:
            run = self.client.get_run(run_id)
            return {
                "run_id": run.info.run_id,
                "status": run.info.status,
                "start_time": run.info.start_time,
                "end_time": run.info.end_time,
                "artifact_uri": run.info.artifact_uri,
            }
        except MlflowException:
            self.logger.warning(f"MLflow run {run_id} not found")
            return {}

    def log_tags(self, tags: Dict[str, str]):
        if not self.run:
            self.logger.warning("No active MLflow run to log tags")
            return
        for key, value in tags.items():
            mlflow.set_tag(key, value)
        self.logger.info(f"Logged MLflow tags: {list(tags.keys())}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_tb, exc_val):
        if self.run_id:
            self.end_run(self.run_id)
