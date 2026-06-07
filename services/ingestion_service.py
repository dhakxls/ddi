"""Ingestion service orchestrating offline pipeline runs."""

from __future__ import annotations

from fastapi import BackgroundTasks, FastAPI

from pipelines import OfflineIngestionConfig
from pipelines.ingestion_fda import run_ingestion as run_fda_ingestion
from pipelines.ingestion_chembl import run_ingestion as run_chembl_ingestion
from .config import ServiceConfig, service_config_from_env


def create_app(config: ServiceConfig | None = None) -> FastAPI:
    if config is None:
        config = service_config_from_env(default_port=8092)
    app = FastAPI(
        title="DDI Ingestion Service",
        version="0.0.1",
        docs_url="/docs" if config.enable_docs else None,
        redoc_url="/redoc" if config.enable_docs else None,
    )

    ingestion_config = OfflineIngestionConfig(project_root=config.project_root)

    @app.get("/healthz")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ingest/fda")
    async def ingest_fda(background_tasks: BackgroundTasks) -> dict[str, str]:
        background_tasks.add_task(run_fda_ingestion, ingestion_config)
        return {"status": "scheduled"}

    @app.post("/ingest/chembl")
    async def ingest_chembl(background_tasks: BackgroundTasks) -> dict[str, str]:
        background_tasks.add_task(run_chembl_ingestion, ingestion_config)
        return {"status": "scheduled"}

    return app
