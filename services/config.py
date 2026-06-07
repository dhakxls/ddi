"""Shared service settings and FastAPI factory utilities."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ServicePaths:
    project_root: Path
    log_dir: Path = field(init=False)
    model_dir: Path = field(init=False)
    data_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        self.log_dir = self.project_root / "logs" / "services"
        self.model_dir = self.project_root / "models" / "artifacts"
        self.data_dir = self.project_root / "data"
        for directory in [self.log_dir]:
            directory.mkdir(parents=True, exist_ok=True)


@dataclass
class ServiceConfig:
    project_root: Path
    host: str = "0.0.0.0"
    port: int = 8080
    reload: bool = False
    enable_docs: bool = True
    model_version: Optional[str] = None

    @property
    def paths(self) -> ServicePaths:
        return ServicePaths(self.project_root)


DEFAULT_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _bool_from_env(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.lower() not in {"0", "false", "no"}


def service_config_from_env(
    *,
    default_port: int,
    model_version_env: str = "SERVICE_MODEL_VERSION",
) -> ServiceConfig:
    project_root = Path(os.environ.get("SERVICE_PROJECT_ROOT", DEFAULT_PROJECT_ROOT))
    host = os.environ.get("SERVICE_HOST", "0.0.0.0")
    port = int(os.environ.get("SERVICE_PORT", default_port))
    reload = _bool_from_env(os.environ.get("SERVICE_RELOAD"), False)
    enable_docs = _bool_from_env(os.environ.get("SERVICE_ENABLE_DOCS"), True)
    model_version = os.environ.get(model_version_env)

    return ServiceConfig(
        project_root=project_root,
        host=host,
        port=port,
        reload=reload,
        enable_docs=enable_docs,
        model_version=model_version,
    )
