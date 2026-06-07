"""Configuration objects for offline data ingestion and feature generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class StoragePaths:
    """Directory layout for ingestion artifacts."""

    project_root: Path
    data_root: Path | None = None
    curated_dir: Path = field(init=False)
    raw_dir: Path = field(init=False)
    cache_dir: Path = field(init=False)
    warehouse_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        base_data_dir = self.data_root or (self.project_root / "data")
        self.curated_dir = base_data_dir / "curated"
        self.raw_dir = base_data_dir / "raw"
        self.cache_dir = base_data_dir / "cache"
        self.warehouse_dir = base_data_dir / "warehouse"

        for directory in [
            self.curated_dir,
            self.raw_dir,
            self.cache_dir,
            self.warehouse_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


@dataclass
class ChunkingConfig:
    """Controls how many records are processed in-memory per batch."""

    max_records_in_memory: int = 256
    max_bytes_in_memory: int = 256 * 1024 * 1024  # 256 MB guard rail

    def should_flush(self, record_count: int, approx_bytes: int) -> bool:
        return (
            record_count >= self.max_records_in_memory
            or approx_bytes >= self.max_bytes_in_memory
        )


@dataclass
class OfflineIngestionConfig:
    """Top-level configuration for the ingestion pipeline."""

    project_root: Path
    chunking: ChunkingConfig = field(default_factory=ChunkingConfig)
    data_root: Path | None = None
    allowed_sources: List[str] = field(
        default_factory=lambda: ["openfda", "pubchem", "chembl", "mychem"]
    )
    offline_only: bool = False

    @property
    def storage(self) -> StoragePaths:
        return StoragePaths(self.project_root, self.data_root)
