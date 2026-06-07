#!/usr/bin/env python3
"""CLI helpers to run offline ingestion pipelines with memory-friendly chunking."""

from __future__ import annotations

from pathlib import Path
import sys

import typer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.settings import ChunkingConfig, OfflineIngestionConfig
from pipelines.ingestion_fda import run_ingestion as run_fda_ingestion
from pipelines.ingestion_chembl import run_ingestion as run_chembl_ingestion
from pipelines.curated_enrichment import merge_annotations_into_curated
from pipelines.manual_seeds import persist_manual_seed_annotations

app = typer.Typer(help="Run FDA and ChEMBL ingestion pipelines")


def _build_config(
    max_records: int,
    max_megabytes: int,
    offline_only: bool,
    output_dir: Path | None,
) -> OfflineIngestionConfig:
    if max_records <= 0:
        raise typer.BadParameter("max-records must be positive")
    if max_megabytes <= 0:
        raise typer.BadParameter("max-mb must be positive")

    chunking = ChunkingConfig(
        max_records_in_memory=max_records,
        max_bytes_in_memory=max_megabytes * 1024 * 1024,
    )
    normalized_output = output_dir.resolve() if output_dir else None

    return OfflineIngestionConfig(
        project_root=PROJECT_ROOT,
        chunking=chunking,
        offline_only=offline_only,
        data_root=normalized_output,
    )


def _run_fda(config: OfflineIngestionConfig) -> None:
    typer.echo("Starting FDA ingestion")
    run_fda_ingestion(config)
    typer.echo("FDA ingestion complete")


def _run_chembl(config: OfflineIngestionConfig) -> None:
    typer.echo("Starting ChEMBL ingestion")
    run_chembl_ingestion(config)
    typer.echo("ChEMBL ingestion complete")


@app.command()
def fda(
    max_records: int = typer.Option(256, help="Max records held in memory before flushing"),
    max_mb: int = typer.Option(256, help="Max megabytes held in memory before flushing"),
    offline_only: bool = typer.Option(False, help="Force offline-only mode for all data sources"),
    output_dir: Path | None = typer.Option(None, help="Optional override for the ingestion output data directory"),
    merge_curated: bool = typer.Option(True, help="Update curated JSON files with extracted enzyme annotations"),
    include_manual_seeds: bool = typer.Option(True, help="Persist manual enzyme annotations for high-priority drugs"),
) -> None:
    """Run only the FDA ingestion pipeline."""
    config = _build_config(max_records, max_mb, offline_only, output_dir)
    if include_manual_seeds:
        persist_manual_seed_annotations(config.storage)
    _run_fda(config)
    if merge_curated:
        updated = merge_annotations_into_curated(config.storage)
        typer.echo(f"Merged annotations into {updated} curated records")


@app.command()
def chembl(
    max_records: int = typer.Option(256, help="Max records held in memory before flushing"),
    max_mb: int = typer.Option(256, help="Max megabytes held in memory before flushing"),
    offline_only: bool = typer.Option(False, help="Force offline-only mode for all data sources"),
    output_dir: Path | None = typer.Option(None, help="Optional override for the ingestion output data directory"),
    merge_curated: bool = typer.Option(True, help="Update curated JSON files with extracted enzyme annotations"),
    include_manual_seeds: bool = typer.Option(True, help="Persist manual enzyme annotations for high-priority drugs"),
) -> None:
    """Run only the ChEMBL ingestion pipeline."""
    config = _build_config(max_records, max_mb, offline_only, output_dir)
    if include_manual_seeds:
        persist_manual_seed_annotations(config.storage)
    _run_chembl(config)
    if merge_curated:
        updated = merge_annotations_into_curated(config.storage)
        typer.echo(f"Merged annotations into {updated} curated records")


@app.command()
def all(
    max_records: int = typer.Option(256, help="Max records held in memory before flushing"),
    max_mb: int = typer.Option(256, help="Max megabytes held in memory before flushing"),
    offline_only: bool = typer.Option(False, help="Force offline-only mode for all data sources"),
    output_dir: Path | None = typer.Option(None, help="Optional override for the ingestion output data directory"),
    merge_curated: bool = typer.Option(True, help="Update curated JSON files with extracted enzyme annotations"),
    include_manual_seeds: bool = typer.Option(True, help="Persist manual enzyme annotations for high-priority drugs"),
) -> None:
    """Run both FDA and ChEMBL ingestion pipelines sequentially."""
    config = _build_config(max_records, max_mb, offline_only, output_dir)
    if include_manual_seeds:
        persist_manual_seed_annotations(config.storage)
    _run_fda(config)
    _run_chembl(config)
    if merge_curated:
        updated = merge_annotations_into_curated(config.storage)
        typer.echo(f"Merged annotations into {updated} curated records")


if __name__ == "__main__":
    app()
