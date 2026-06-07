"""Shared helpers for building enzyme annotations from multiple sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

from .settings import StoragePaths

KNOWN_ENZYMES = [
    "CYP1A2",
    "CYP2B6",
    "CYP2C8",
    "CYP2C9",
    "CYP2C19",
    "CYP2D6",
    "CYP2E1",
    "CYP3A4",
    "CYP3A5",
    "CYP3A7",
    "UGT1A1",
    "UGT2B7",
]


@dataclass
class EnzymeAnnotation:
    compound_key: str
    display_name: str
    enzyme_name: str
    category: str  # substrate|inhibition|induction
    source: str
    evidence: Optional[str] = None
    references: list[str] = field(default_factory=list)
    identifiers: Dict[str, str] = field(default_factory=dict)


def normalize_name(value: str | None) -> str:
    return (value or "").strip().lower()


def update_annotation_index(
    annotations: Dict[str, Dict[str, Any]],
    annotation: EnzymeAnnotation,
) -> None:
    entry = annotations.setdefault(
        annotation.compound_key,
        {
            "display_name": annotation.display_name or annotation.compound_key,
            "synonyms": set({annotation.display_name.lower()} if annotation.display_name else {}),
            "identifiers": {},
            "enzyme_data": {
                "substrate": {},
                "inhibition": {},
                "induction": {},
            },
        },
    )
    entry["synonyms"].add(annotation.display_name.lower())
    for key, value in annotation.identifiers.items():
        if value:
            entry["identifiers"].setdefault(key, value)

    payload = {
        "source": annotation.source,
        "evidence": annotation.evidence,
        "references": annotation.references,
    }
    entry["enzyme_data"][annotation.category][annotation.enzyme_name] = payload


def persist_annotations(
    annotations: Dict[str, Dict[str, Any]],
    storage: StoragePaths,
    *,
    source: str,
) -> None:
    annotations_dir = storage.warehouse_dir / "enzyme_annotations"
    annotations_dir.mkdir(parents=True, exist_ok=True)
    output_path = annotations_dir / f"{source}_annotations.json"

    payload = {
        "source": source,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "records": [],
    }

    for compound_key, entry in sorted(annotations.items()):
        payload["records"].append(
            {
                "compound_key": compound_key,
                "display_name": entry.get("display_name", compound_key),
                "synonyms": sorted(entry.get("synonyms", [])),
                "identifiers": entry.get("identifiers", {}),
                "enzyme_data": entry.get("enzyme_data", {}),
            }
        )

    with open(output_path, "w") as fh:
        import json

        json.dump(payload, fh, indent=2)
