"""Offline FDA Structured Product Label ingestion pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional, Dict
import json
import zipfile

from .enzyme_annotations import (
    EnzymeAnnotation,
    KNOWN_ENZYMES,
    normalize_name,
    persist_annotations,
    update_annotation_index,
)

from .settings import OfflineIngestionConfig, StoragePaths


@dataclass
class FDASPLRecord:
    """Subset of fields extracted from SPL for metabolism analysis."""

    spl_id: str
    product_name: str
    clinical_pharmacology: str
    metabolism_section: Optional[str]
    raw_path: Path


def iter_spl_archives(raw_dir: Path) -> Iterator[Path]:
    """Yield SPL archive files stored under data/raw/fda."""

    spl_dir = raw_dir / "fda"
    if not spl_dir.exists():
        return
    for archive in sorted(spl_dir.glob("*.zip")):
        if archive.is_file():
            yield archive


def extract_spl_records(archive_path: Path) -> Iterable[FDASPLRecord]:
    """Stream SPL XML files from a ZIP archive and yield extracted metadata."""

    with zipfile.ZipFile(archive_path) as zf:
        for xml_name in zf.namelist():
            if not xml_name.lower().endswith(".xml"):
                continue
            with zf.open(xml_name) as xml_file:
                xml_bytes = xml_file.read()  # SPL files are typically < 5 MB
                yield FDASPLRecord(
                    spl_id=xml_name,
                    product_name="",  # placeholder until parser implemented
                    clinical_pharmacology=xml_bytes.decode(errors="ignore"),
                    metabolism_section=None,
                    raw_path=archive_path,
                )


def run_ingestion(config: OfflineIngestionConfig) -> None:
    """Entry point for FDA SPL ingestion respecting chunk limits."""

    storage = config.storage
    records_buffer: list[FDASPLRecord] = []
    approx_bytes = 0
    annotations: Dict[str, Dict] = {}

    for archive in iter_spl_archives(storage.raw_dir):
        for record in extract_spl_records(archive):
            records_buffer.append(record)
            approx_bytes += len(record.clinical_pharmacology.encode("utf-8"))

            product_name = infer_product_name(record)
            text_blob = "\n".join(filter(None, [record.clinical_pharmacology, record.metabolism_section or ""]))
            for enzyme_name, category, evidence in extract_enzyme_mentions(text_blob):
                annotation = EnzymeAnnotation(
                    compound_key=normalize_name(product_name or record.spl_id),
                    display_name=product_name or record.spl_id,
                    enzyme_name=enzyme_name,
                    category=category,
                    source="fda_spl",
                    evidence=evidence,
                    references=[record.spl_id],
                )
                update_annotation_index(annotations, annotation)

            if config.chunking.should_flush(len(records_buffer), approx_bytes):
                persist_chunk(records_buffer, storage)
                records_buffer.clear()
                approx_bytes = 0

    if records_buffer:
        persist_chunk(records_buffer, storage)

    persist_annotations(annotations, storage, source="fda_spl")


def persist_chunk(records: list[FDASPLRecord], storage: StoragePaths) -> None:
    """Write a chunk of records to the warehouse directory."""

    warehouse = storage.warehouse_dir / "fda_spl"
    warehouse.mkdir(parents=True, exist_ok=True)
    output_path = warehouse / f"chunk_{len(list(warehouse.glob('chunk_*.json'))):04d}.json"
    with open(output_path, "w") as f:
        json.dump([record.__dict__ for record in records], f, indent=2)


def infer_product_name(record: FDASPLRecord) -> str:
    # Attempt simple extraction from filename (before first dash/underscore)
    candidate = Path(record.spl_id).stem
    if candidate:
        return candidate.replace("_", " ").replace("-", " ").title()
    return record.spl_id


def extract_enzyme_mentions(text: str) -> list[tuple[str, str, str]]:
    mentions: list[tuple[str, str, str]] = []
    lowered = text.lower()
    for enzyme in KNOWN_ENZYMES:
        idx = lowered.find(enzyme.lower())
        if idx == -1:
            continue
        window_start = max(0, idx - 160)
        window_end = min(len(text), idx + 160)
        window = text[window_start:window_end]
        category = infer_category(window)
        mentions.append((enzyme, category, window.strip()))
    return mentions


def infer_category(snippet: str) -> str:
    lowered = snippet.lower()
    if any(token in lowered for token in ["substrate", "metabolized", "metabolism"]):
        return "substrate"
    if any(token in lowered for token in ["inhibitor", "inhibits", "inhibition", "blocker"]):
        return "inhibition"
    if any(token in lowered for token in ["inducer", "induces", "induction"]):
        return "induction"
    return "substrate"
