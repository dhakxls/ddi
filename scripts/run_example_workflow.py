#!/usr/bin/env python3
"""CLI helper to run an end-to-end fetch + DDI prediction example."""

from __future__ import annotations

import json
import os
from typing import Dict, Any

import requests
import typer

DEFAULT_UI_URL = os.environ.get("UI_BASE_URL", "http://localhost:8084")
DEFAULT_PREDICTION_URL = os.environ.get("PREDICTION_SERVICE_URL", "http://localhost:8090")

app = typer.Typer(help="Run example workflows against the modular services")


def _fetch_drug(ui_url: str, drug_name: str) -> Dict[str, Any]:
    typer.echo(f"Fetching {drug_name} from {ui_url}")
    response = requests.get(f"{ui_url}/api/fetch/drug/{drug_name}", timeout=60)
    response.raise_for_status()
    payload = response.json()
    typer.echo(json.dumps(payload, indent=2))
    return payload


def _compound_payload(drug_data: Dict[str, Any]) -> Dict[str, Any]:
    enzyme_data = drug_data.get("enzyme_data") or {}
    return {
        "compound_name": drug_data.get("compound_name"),
        "substrate_data": enzyme_data.get("substrate", {}),
        "inhibition_data": enzyme_data.get("inhibition", {}),
        "induction_data": enzyme_data.get("induction", {}),
    }


def _predict_enzyme(prediction_url: str, compound: Dict[str, Any]) -> None:
    typer.echo(f"Calling /predict/enzyme for {compound['compound_name']}")
    response = requests.post(
        f"{prediction_url}/predict/enzyme",
        json=compound,
        timeout=60,
    )
    response.raise_for_status()
    typer.echo(json.dumps(response.json(), indent=2))


def _predict_ddi(prediction_url: str, drug_a_payload: Dict[str, Any], drug_b_payload: Dict[str, Any]) -> None:
    typer.echo("Calling /predict/ddi")
    response = requests.post(
        f"{prediction_url}/predict/ddi",
        json={"drug_a": drug_a_payload, "drug_b": drug_b_payload},
        timeout=60,
    )
    response.raise_for_status()
    typer.echo(json.dumps(response.json(), indent=2))


@app.command()
def run(
    drug_a: str = typer.Option(..., help="Name of the first drug"),
    drug_b: str = typer.Option(..., help="Name of the second drug"),
    ui_url: str = typer.Option(DEFAULT_UI_URL, help="Base URL of the UI service"),
    prediction_url: str = typer.Option(DEFAULT_PREDICTION_URL, help="Base URL of the prediction service"),
    skip_enzyme_preds: bool = typer.Option(False, help="Skip the per-drug /predict/enzyme calls"),
):
    """Fetch two drugs and run a DDI prediction using their auto-populated enzyme data."""

    drug_a_data = _fetch_drug(ui_url, drug_a)
    drug_b_data = _fetch_drug(ui_url, drug_b)

    drug_a_payload = _compound_payload(drug_a_data)
    drug_b_payload = _compound_payload(drug_b_data)

    if not skip_enzyme_preds:
        _predict_enzyme(prediction_url, drug_a_payload)
        _predict_enzyme(prediction_url, drug_b_payload)

    _predict_ddi(prediction_url, drug_a_payload, drug_b_payload)


if __name__ == "__main__":
    app()
