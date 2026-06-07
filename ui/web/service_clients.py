"""HTTP clients for internal DDI services."""

from __future__ import annotations

from typing import Any, Dict

import httpx


class PredictionServiceClient:
    def __init__(self, base_url: str, timeout: float = 15.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def predict_enzyme(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._post("/predict/enzyme", payload)

    async def predict_ddi(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._post("/predict/ddi", payload)

    async def recommend_validation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._post("/recommend/validation", payload)

    async def health(self) -> Dict[str, Any]:
        return await self._get("/healthz")

    async def metadata(self) -> Dict[str, Any]:
        return await self._get("/metadata")

    async def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def _get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()


class FeatureServiceClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def get_features(self, compound_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/features/{compound_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def health(self) -> Dict[str, Any]:
        url = f"{self.base_url}/healthz"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()
