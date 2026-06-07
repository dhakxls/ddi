#!/usr/bin/env python3
"""Utility CLI for running modular DDI services locally."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
import socket

import typer

REPO_ROOT = Path(__file__).parent.parent.resolve()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipelines.manual_seeds import (
    persist_manual_seed_annotations,
    validate_all_seed_entries,
    validate_manual_seed_entry,
    validate_manual_seed_records,
)
from pipelines.settings import StoragePaths
from pipelines.llm_seed import LLMSeedConfig, LLMSeedGenerator

app = typer.Typer(help="Manage modular FastAPI services")

DEFAULT_SERVICE_PORTS = [
    ("prediction", 8090),
    ("feature", 8091),
    ("ingestion", 8092),
    ("ui", 8084),
]


def _run_uvicorn(
    module: str,
    host: str,
    port: int,
    app_path: str,
    factory: bool = False,
    extra_env: dict[str, str] | None = None,
) -> None:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        f"{module}:{app_path}",
    ]
    if factory:
        command.append("--factory")
    command.extend(["--host", host, "--port", str(port)])

    typer.echo(f"Running {' '.join(command)}")
    subprocess.run(command, cwd=REPO_ROOT, env=env, check=True)


@app.command()
def prediction(host: str = "0.0.0.0", port: int = 8090):
    """Start the prediction service."""
    _run_uvicorn("services.prediction_service", host, port, "create_app", factory=True)


@app.command()
def feature(host: str = "0.0.0.0", port: int = 8091):
    """Start the feature service."""
    _run_uvicorn("services.feature_service", host, port, "create_app", factory=True)


@app.command()
def ingestion(host: str = "0.0.0.0", port: int = 8092):
    """Start the ingestion service."""
    _run_uvicorn("services.ingestion_service", host, port, "create_app", factory=True)


def _run_repo_script(script_relative: str, *args: str) -> None:
    script_path = REPO_ROOT / script_relative
    command = [sys.executable, str(script_path), *args]
    typer.echo(f"Running {' '.join(command)}")
    subprocess.run(command, cwd=REPO_ROOT, check=True)


def _port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()


@app.command()
def ui(
    host: str = "0.0.0.0",
    port: int = 8084,
    prediction_url: str = "http://localhost:8090",
    feature_url: str = "http://localhost:8091",
):
    """Start the UI with URLs pointing to the modular services."""
    extra_env = {
        "PREDICTION_SERVICE_URL": prediction_url,
        "FEATURE_SERVICE_URL": feature_url,
    }
    env = os.environ.copy()
    env.update(extra_env)
    _run_uvicorn(
        "ui.web.app",
        host,
        port,
        "app",
        factory=False,
        extra_env=extra_env,
    )


@app.command()
def check():
    """Run health checks against all services."""
    _run_repo_script("scripts/check_services.py")


@app.command()
def ingest(
    source: str = typer.Option("all", "-s", "--source", help="Choose which pipeline to run (fda, chembl, all)", case_sensitive=False),
    max_records: int = typer.Option(256, help="Max records held in memory before flushing"),
    max_mb: int = typer.Option(256, help="Max megabytes held in memory before flushing"),
    offline_only: bool = typer.Option(False, help="Force offline-only mode for all data sources"),
    output_dir: Path | None = typer.Option(None, help="Optional override for the ingestion output data directory"),
    merge_curated: bool = typer.Option(True, help="Update curated JSON files after ingestion"),
):
    """Run the offline ingestion pipelines."""
    normalized = source.lower()
    if normalized not in {"fda", "chembl", "all"}:
        raise typer.BadParameter("source must be one of: fda, chembl, all")

    args = [normalized, f"--max-records={max_records}", f"--max-mb={max_mb}"]
    if offline_only:
        args.append("--offline-only")
    if output_dir:
        args.append(f"--output-dir={output_dir}")
    if not merge_curated:
        args.append("--no-merge-curated")
    _run_repo_script("scripts/run_ingestion.py", *args)


@app.command("seed-annotations")
def seed_annotations(
    output_dir: Path | None = typer.Option(
        None,
        help="Optional override for the data directory that receives manual annotations",
    )
):
    """Persist manual enzyme annotations without running the ingestion pipelines."""

    normalized_output = output_dir.resolve() if output_dir else None
    storage = StoragePaths(REPO_ROOT, normalized_output)
    output_path = persist_manual_seed_annotations(storage)
    typer.echo(f"Wrote manual enzyme annotations to {output_path}")


@app.command("validate-seeds")
def validate_seeds():
    """Run validation checks against manual seed annotations without writing files."""

    errors = validate_manual_seed_records()
    if errors:
        bullet_list = "\n - ".join(errors)
        raise typer.Exit(code=1, message=f"Manual seed validation failed:\n - {bullet_list}")

    typer.echo("Manual seed annotations validated successfully")


@app.command()
def status(host: str = "127.0.0.1"):
    """Show whether default service ports are accepting connections."""
    typer.echo("Service port status (host %s):" % host)
    for name, port in DEFAULT_SERVICE_PORTS:
        online = _port_open(host, port)
        state = "ONLINE" if online else "offline"
        typer.echo(f"  {name:>10} : {port} -> {state}")


@app.command("llm-generate-seed")
def llm_generate_seed(
    drug_name: str = typer.Argument(..., help="Drug name to curate"),
    context_file: Path | None = typer.Option(
        None,
        help="Optional path to a text file with additional context (e.g., SPL excerpt)",
    ),
    model_path: Path = typer.Option(
        _default_model_path(),
        help="Path to a local gguf/ggml LLaMA-family model",
    ),
    output_dir: Path | None = typer.Option(
        None,
        help="Directory where generated JSON should be stored (defaults to data/llm_curation)",
    ),
):
    """Generate a seed annotation via llama-cpp and save it for later validation."""

    context = context_file.read_text() if context_file else None
    generator = LLMSeedGenerator(LLMSeedConfig(model_path=model_path))
    entry = generator.generate_seed_entry(drug_name, context)

    errors = validate_manual_seed_entry(entry)
    if errors:
        bullet_list = "\n - ".join(errors)
        raise typer.Exit(code=1, message=f"Generated entry failed validation:\n - {bullet_list}")

    llm_dir = output_dir or (REPO_ROOT / "data" / "llm_curation")
    llm_dir.mkdir(parents=True, exist_ok=True)
    output_path = llm_dir / f"{drug_name.lower().replace(' ', '_')}_seed.json"
    with open(output_path, "w") as fh:
        json.dump(entry, fh, indent=2)

    typer.echo(f"Saved generated seed to {output_path}")


@app.command("llm-validate-all")
def llm_validate_all(
    data_root: Path | None = typer.Option(None, help="Optional root to search for llm_curation entries"),
):
    """Validate curated + LLM-generated entries together."""

    storage = StoragePaths(REPO_ROOT, data_root)
    errors = validate_all_seed_entries(storage)
    if errors:
        bullet_list = "\n - ".join(errors)
        raise typer.Exit(code=1, message=f"Validation failed:\n - {bullet_list}")

    typer.echo("All curated + LLM-generated seed entries are valid")


if __name__ == "__main__":
    app()


def _default_model_path() -> Path:
    return REPO_ROOT / "models" / "llms" / "llama-7b" / "ggml-model-q4_0.gguf"
