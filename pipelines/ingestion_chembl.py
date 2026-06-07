"""Offline ChEMBL target ingestion pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Dict
import csv

from .enzyme_annotations import (
    EnzymeAnnotation,
    normalize_name,
    persist_annotations,
    update_annotation_index,
)
from .settings import OfflineIngestionConfig, StoragePaths


@dataclass
class ChEMBLTargetRecord:
    """Subset of ChEMBL fields needed for enzyme interactions."""

    chembl_id: str
    pref_name: str
    target_type: str
    organism: str
    accession: Optional[str]
    symbol: Optional[str]
    source_file: Path


def _categorize_action(action_type: str, mechanism: str) -> Optional[str]:
    text = " ".join([action_type or "", mechanism or ""]).lower()
    if any(token in text for token in ["substrate", "metabolized", "metabolism"]):
        return "substrate"
    if any(token in text for token in ["inhibitor", "inhibition", "inhibits", "blocker"]):
        return "inhibition"
    if any(token in text for token in ["inducer", "induction", "induces"]):
        return "induction"
    return None


def iter_chembl_exports(raw_dir: Path) -> Iterator[Path]:
    """Yield gzipped TSV exports located under data/raw/chembl."""

    chembl_dir = raw_dir / "chembl"
    if not chembl_dir.exists():
        return

    for tsv in sorted(chembl_dir.glob("*.tsv")):
        if tsv.is_file():
            yield tsv


def run_ingestion(config: OfflineIngestionConfig) -> None:
    """Entry point for ChEMBL target ingestion with enzyme annotations."""

    storage = config.storage
    chunk: list[ChEMBLTargetRecord] = []
    approx_bytes = 0
    annotations: Dict[str, Dict] = {}

    for export_path in iter_chembl_exports(storage.raw_dir):
        with open(export_path, "r") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                record = ChEMBLTargetRecord(
                    chembl_id=row.get("chembl_id", ""),
                    pref_name=row.get("pref_name", ""),
                    target_type=row.get("target_type", ""),
                    organism=row.get("organism", ""),
                    accession=row.get("accession"),
                    symbol=row.get("symbol"),
                    source_file=export_path,
                )
                chunk.append(record)
                approx_bytes += sum(len(str(value)) for value in row.values())

                action_category = _categorize_action(row.get("action_type", ""), row.get("mechanism_of_action", ""))
                enzyme_name = row.get("target_pref_name") or row.get("target_name") or row.get("target_chembl_id")
                compound_name = row.get("molecule_pref_name") or row.get("drug_name") or record.pref_name
                if action_category and enzyme_name and compound_name:
                    annotation = EnzymeAnnotation(
                        compound_key=normalize_name(compound_name),
                        display_name=compound_name.strip(),
                        enzyme_name=enzyme_name.strip(),
                        category=action_category,
                        source="ChEMBL",
                        evidence=row.get("mechanism_of_action") or row.get("description"),
                        references=[value for key, value in row.items() if key.startswith("reference") and value],
                        identifiers={"chembl_id": row.get("molecule_chembl_id") or record.chembl_id},
                    )
                    update_annotation_index(annotations, annotation)

                if config.chunking.should_flush(len(chunk), approx_bytes):
                    persist_chunk(chunk, storage)
                    chunk.clear()
                    approx_bytes = 0

    if chunk:
        persist_chunk(chunk, storage)

    persist_annotations(annotations, storage, source="chembl")


def persist_chunk(records: list[ChEMBLTargetRecord], storage: StoragePaths) -> None:
    """Write target records to warehouse batches."""

    warehouse = storage.warehouse_dir / "chembl_targets"
    warehouse.mkdir(parents=True, exist_ok=True)
    existing = len(list(warehouse.glob("chunk_*.json")))
    output_path = warehouse / f"chunk_{existing:04d}.json"

    with open(output_path, "w") as f:
        import json

        json.dump([record.__dict__ for record in records], f, indent=2)
