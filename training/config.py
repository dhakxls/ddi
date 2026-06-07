"""Training configuration objects for model pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class TrainingPaths:
    project_root: Path
    artifacts_dir: Path = field(init=False)
    datasets_dir: Path = field(init=False)
    models_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        self.artifacts_dir = self.project_root / "artifacts"
        self.datasets_dir = self.project_root / "data" / "datasets"
        self.models_dir = self.project_root / "models" / "artifacts"
        self.logs_dir = self.project_root / "logs" / "training"

        for directory in [
            self.artifacts_dir,
            self.datasets_dir,
            self.models_dir,
            self.logs_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


@dataclass
class TrainerConfig:
    project_root: Path
    experiment_name: str
    seed: int = 42
    batch_size: int = 64
    num_workers: int = 4
    fp16: bool = True
    features: List[str] = field(
        default_factory=lambda: [
            "rdkit_descriptors",
            "morgan_fingerprints",
            "pk_features",
        ]
    )

    @property
    def paths(self) -> TrainingPaths:
        return TrainingPaths(self.project_root)
