"""Trainer for the dominant enzyme classifier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from .config import TrainerConfig


@dataclass
class DominantEnzymeDataset:
    features: pd.DataFrame
    labels: pd.DataFrame

    @classmethod
    def load_from_parquet(cls, dataset_path: Path) -> "DominantEnzymeDataset":
        features = pd.read_parquet(dataset_path / "features.parquet")
        labels = pd.read_parquet(dataset_path / "labels.parquet")
        return cls(features, labels)


class DominantEnzymeTrainer:
    def __init__(self, config: TrainerConfig, dataset_dir: Path):
        self.config = config
        self.paths = config.paths
        self.dataset = DominantEnzymeDataset.load_from_parquet(dataset_dir)

    def train(self) -> None:
        """Placeholder for training loop."""

        # TODO: integrate LightGBM or Chemprop training here
        print(
            f"Training dominant enzyme model with {len(self.dataset.features)} samples"
        )

    def save(self, model_name: str) -> Path:
        output_path = self.paths.models_dir / f"{model_name}.bin"
        with open(output_path, "wb") as handle:
            handle.write(b"placeholder")
        return output_path
