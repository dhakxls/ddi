"""Helpers to enrich curated compound JSON files with enzyme annotations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from .enzyme_annotations import normalize_name
from .settings import StoragePaths


def merge_annotations_into_curated(storage: StoragePaths) -> int:
    """Merge enzyme annotation payloads into curated JSON files.

    Returns the number of curated files updated.
    """

    annotations_dir = storage.warehouse_dir / "enzyme_annotations"
    if not annotations_dir.exists():
        return 0

    annotations_index: Dict[str, Dict[str, Any]] = {}
    for path in annotations_dir.glob("*_annotations.json"):
        with open(path, "r") as fh:
            payload = json.load(fh)
        for record in payload.get("records", []):
            key = record.get("compound_key")
            if not key:
                continue
            entry = annotations_index.setdefault(key, {
                "synonyms": set(record.get("synonyms", [])),
                "enzyme_data": {
                    "substrate": {},
                    "inhibition": {},
                    "induction": {},
                },
                "sources": set(),
            })
            entry["synonyms"].update(record.get("synonyms", []))
            entry["sources"].add(payload.get("source", "unknown"))
            for category, enzymes in record.get("enzyme_data", {}).items():
                entry["enzyme_data"].setdefault(category, {})
                entry["enzyme_data"][category].update(enzymes)

    if not annotations_index:
        return 0

    updated = 0
    curated_dir = storage.curated_dir
    curated_dir.mkdir(parents=True, exist_ok=True)
    for json_path in curated_dir.glob("*.json"):
        with open(json_path, "r") as fh:
            data = json.load(fh)

        compound_key = normalize_name(data.get("compound_name") or data.get("compound_id") or json_path.stem)
        match = annotations_index.get(compound_key)
        if not match:
            continue

        enzyme_data = data.setdefault("enzyme_data", {
            "substrate": {},
            "inhibition": {},
            "induction": {},
        })

        for category, enzymes in match["enzyme_data"].items():
            category_bucket = enzyme_data.setdefault(category, {})
            for enzyme_name, payload in enzymes.items():
                if enzyme_name in category_bucket:
                    continue  # preserve curated overrides
                mapped = {
                    "source": payload.get("source", "annotations"),
                    "evidence": payload.get("evidence"),
                }
                if category == "substrate":
                    mapped["is_substrate"] = True
                if category == "inhibition":
                    mapped["is_inhibitor"] = True
                if category == "induction":
                    mapped["is_inducer"] = True
                category_bucket[enzyme_name] = mapped

        sources = data.setdefault("sources", [])
        for source in sorted(match["sources"]):
            if source not in sources:
                sources.append(source)

        with open(json_path, "w") as fh:
            json.dump(data, fh, indent=2)
        updated += 1

    return updated
