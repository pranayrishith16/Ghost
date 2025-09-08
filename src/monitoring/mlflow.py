import os
from typing import Dict, Any, Optional
import mlflow

from config.settings import get_config
from src.interfaces.monitor import MonitorInterface

class MLFlowMonitor(MonitorInterface):
    def __init__(self) -> None:
        cfg = get_config().monitoring
        mlflow.set_tracking_uri(cfg.tracking_uri)
        self.experiment_name = cfg.experiment_name
        mlflow.set_experiment(self.experiment_name)
        self._run: Optional[mlflow.ActiveRun] = None
        # Lazily start run to allow caller to control scope if needed
        if mlflow.active_run() is None:
            self._run = mlflow.start_run(run_name=self.experiment_name)

    def log_metrics(self, metrics: Dict[str, Any], step: int | None = None) -> None:
        mlflow.log_metrics({k: float(v) for k, v in metrics.items() if isinstance(v, (int, float))}, step=step)

    def log_artifact(self, path: str, artifact_path: str | None = None) -> None:
        if os.path.exists(path):
            mlflow.log_artifact(path, artifact_path=artifact_path)

    def __del__(self) -> None:
        try:
            if self._run is not None:
                mlflow.end_run()
        except Exception:
            pass
