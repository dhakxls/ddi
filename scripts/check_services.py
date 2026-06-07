#!/usr/bin/env python3
"""Quick health-check script for modular DDI services."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List

import httpx


@dataclass
class ServiceTarget:
    name: str
    url: str


SERVICES: List[ServiceTarget] = [
    ServiceTarget("prediction", "http://localhost:8090/healthz"),
    ServiceTarget("feature", "http://localhost:8091/healthz"),
    ServiceTarget("ingestion", "http://localhost:8092/healthz"),
    ServiceTarget("ui", "http://localhost:8084/api/health"),
]


async def check_service(client: httpx.AsyncClient, target: ServiceTarget) -> None:
    try:
        response = await client.get(target.url, timeout=5.0)
        response.raise_for_status()
        print(f"✅ {target.name} OK: {response.json()}")
    except Exception as exc:
        print(f"❌ {target.name} FAILED: {exc}")


async def main() -> None:
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*(check_service(client, target) for target in SERVICES))


if __name__ == "__main__":
    asyncio.run(main())
