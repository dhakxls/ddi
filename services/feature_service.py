"""Feature service exposing curated dataset slices for downstream models."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .config import ServiceConfig, service_config_from_env
from .feature_loader import CompoundStore


def create_app(config: ServiceConfig | None = None) -> FastAPI:
    if config is None:
        config = service_config_from_env(default_port=8091)
    app = FastAPI(
        title="DDI Feature Service",
        version="0.0.1",
        docs_url="/docs" if config.enable_docs else None,
        redoc_url="/redoc" if config.enable_docs else None,
    )

    store = CompoundStore(config.paths.project_root / "data" / "curated")

    @app.get("/healthz")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/features/{compound_id}")
    async def fetch_features(compound_id: str) -> dict:
        record = store.load_compound(compound_id)
        if not record:
            raise HTTPException(status_code=404, detail="Compound not found")
        return {
            "compound_id": record.compound_id,
            "features": record.features,
        }

    return app
