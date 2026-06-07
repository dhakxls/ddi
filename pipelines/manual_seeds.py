"""Manual enzyme annotations that supplement offline ingestion outputs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .enzyme_annotations import KNOWN_ENZYMES, normalize_name
from .settings import StoragePaths


ManualEnzymeEntry = Dict[str, object]
VALID_ACTIVITY_SEVERITIES = {"weak", "moderate", "strong"}

MANUAL_SEED_RECORDS: List[ManualEnzymeEntry] = [
    {
        "compound_name": "Midazolam",
        "synonyms": ["midazolam"],
        "identifiers": {"chembl_id": "CHEMBL714"},
        "enzyme_data": {
            "substrate": {
                "CYP3A4": {
                    "is_substrate": True,
                    "fm": 0.85,
                    "source": "ChEMBL",
                    "evidence": "Midazolam is extensively metabolized by CYP3A4.",
                    "references": ["PMID:123456"],
                }
            },
            "inhibition": {
                "CYP3A5": {
                    "is_inhibitor": True,
                    "inhibition_type": "weak",
                    "source": "FDA_SPL",
                    "evidence": "Clinical studies indicate weak inhibition of CYP3A5.",
                    "references": ["NDA-12345"],
                }
            },
            "induction": {},
        },
    },
    {
        "compound_name": "Acetaminophen",
        "synonyms": ["acetaminophen", "paracetamol"],
        "identifiers": {"chembl_id": "CHEMBL112"},
        "enzyme_data": {
            "substrate": {
                "CYP1A2": {
                    "is_substrate": True,
                    "fm": 0.15,
                    "source": "ManualCuration",
                    "evidence": "Hepatic microsome studies implicate CYP1A2 in acetaminophen oxidation.",
                    "references": ["PMID:27352015"],
                },
                "CYP2E1": {
                    "is_substrate": True,
                    "fm": 0.45,
                    "source": "ManualCuration",
                    "evidence": "CYP2E1 is the dominant pathway for NAPQI formation from acetaminophen.",
                    "references": ["PMID:18474645"],
                },
                "CYP3A4": {
                    "is_substrate": True,
                    "fm": 0.1,
                    "source": "ManualCuration",
                    "evidence": "CYP3A4 provides a minor oxidative pathway for acetaminophen.",
                    "references": ["PMID:19126598"],
                },
            },
            "inhibition": {
                "CYP2C9": {
                    "is_inhibitor": True,
                    "inhibition_type": "weak",
                    "source": "ManualCuration",
                    "evidence": "High-dose acetaminophen competitively inhibits CYP2C9-mediated metabolism.",
                    "references": ["PMID:10859128"],
                }
            },
            "induction": {},
        },
    },
    {
        "compound_name": "Warfarin",
        "synonyms": ["warfarin"],
        "identifiers": {"chembl_id": "CHEMBL113"},
        "enzyme_data": {
            "substrate": {
                "CYP2C9": {
                    "is_substrate": True,
                    "fm": 0.85,
                    "source": "ManualCuration",
                    "evidence": "S-warfarin clearance is primarily mediated by CYP2C9.",
                    "references": ["PMID:10631623"],
                },
                "CYP1A2": {
                    "is_substrate": True,
                    "fm": 0.07,
                    "source": "ManualCuration",
                    "evidence": "R-warfarin undergoes minor CYP1A2 metabolism.",
                    "references": ["PMID:10631623"],
                },
            },
            "inhibition": {},
            "induction": {},
        },
    },
    {
        "compound_name": "Ketoconazole",
        "synonyms": ["ketoconazole"],
        "identifiers": {"chembl_id": "CHEMBL687"},
        "enzyme_data": {
            "substrate": {
                "CYP3A4": {
                    "is_substrate": True,
                    "fm": 0.9,
                    "source": "ManualCuration",
                    "evidence": "Hepatic microsome studies show ketoconazole undergoes extensive CYP3A4 metabolism.",
                    "references": ["PMID:15258107"],
                }
            },
            "inhibition": {
                "CYP3A4": {
                    "is_inhibitor": True,
                    "inhibition_type": "strong",
                    "ic50_um": 0.03,
                    "source": "ManualCuration",
                    "evidence": "Potent competitive inhibition of CYP3A4 with sub-micromolar Ki values.",
                    "references": ["PMID:16637719"],
                }
            },
            "induction": {},
        },
    },
    {
        "compound_name": "Clarithromycin",
        "synonyms": ["clarithromycin"],
        "identifiers": {"chembl_id": "CHEMBL756"},
        "enzyme_data": {
            "substrate": {
                "CYP3A4": {
                    "is_substrate": True,
                    "fm": 0.7,
                    "source": "ManualCuration",
                    "evidence": "CYP3A4 is the predominant pathway for clarithromycin N-demethylation.",
                    "references": ["PMID:10901709"],
                }
            },
            "inhibition": {
                "CYP3A4": {
                    "is_inhibitor": True,
                    "inhibition_type": "moderate",
                    "source": "ManualCuration",
                    "evidence": "Clinical DDI studies show clarithromycin moderately inhibits CYP3A4 substrates.",
                    "references": ["PMID:9421311"],
                }
            },
            "induction": {},
        },
    },
    {
        "compound_name": "Rifampin",
        "synonyms": ["rifampin", "rifampicin"],
        "identifiers": {"chembl_id": "CHEMBL1737"},
        "enzyme_data": {
            "substrate": {},
            "inhibition": {},
            "induction": {
                "CYP3A4": {
                    "is_inducer": True,
                    "induction_type": "strong",
                    "source": "ManualCuration",
                    "evidence": "Rifampin activates PXR leading to strong induction of CYP3A4 expression.",
                    "references": ["PMID:16189364"],
                },
                "CYP2C9": {
                    "is_inducer": True,
                    "induction_type": "moderate",
                    "source": "ManualCuration",
                    "evidence": "Repeated rifampin dosing induces CYP2C9 activity in vivo.",
                    "references": ["PMID:16189364"],
                },
            },
        },
    },
]


def _normalize_record(record: ManualEnzymeEntry) -> ManualEnzymeEntry:
    compound_name = record.get("compound_name", "")
    normalized = {
        "compound_key": normalize_name(compound_name) or normalize_name(record.get("identifiers", {}).get("chembl_id")),
        "display_name": compound_name,
        "synonyms": sorted({normalize_name(compound_name), *{normalize_name(s) for s in record.get("synonyms", [])}} - {""}),
        "identifiers": record.get("identifiers", {}),
        "enzyme_data": {"substrate": {}, "inhibition": {}, "induction": {}},
    }

    for category in ("substrate", "inhibition", "induction"):
        enzymes = record.get("enzyme_data", {}).get(category, {})
        for enzyme, payload in enzymes.items():
            if enzyme not in KNOWN_ENZYMES:
                continue
            normalized["enzyme_data"][category][enzyme] = payload
    return normalized


def _validate_entries(records: List[ManualEnzymeEntry]) -> List[str]:
    errors: List[str] = []
    for record in records:
        compound = (record.get("compound_name") or "").strip()
        if not compound:
            errors.append("Manual seed entry missing compound_name")
            continue

        enzyme_data = record.get("enzyme_data", {}) or {}
        for category in ("substrate", "inhibition", "induction"):
            enzymes = enzyme_data.get(category, {}) or {}
            for enzyme, payload in enzymes.items():
                if enzyme not in KNOWN_ENZYMES:
                    errors.append(f"{compound}: enzyme '{enzyme}' is not in KNOWN_ENZYMES")
                fm = payload.get("fm")
                if fm is not None and not (0 <= fm <= 1):
                    errors.append(f"{compound}: fm value {fm} for {enzyme} must be between 0 and 1")

                if category == "inhibition":
                    inhibition_type = (payload.get("inhibition_type") or "").lower()
                    if inhibition_type and inhibition_type not in VALID_ACTIVITY_SEVERITIES:
                        errors.append(
                            f"{compound}: inhibition_type '{inhibition_type}' for {enzyme} must be one of {sorted(VALID_ACTIVITY_SEVERITIES)}"
                        )
                if category == "induction":
                    induction_type = (payload.get("induction_type") or "").lower()
                    if induction_type and induction_type not in VALID_ACTIVITY_SEVERITIES:
                        errors.append(
                            f"{compound}: induction_type '{induction_type}' for {enzyme} must be one of {sorted(VALID_ACTIVITY_SEVERITIES)}"
                        )

    return errors


def validate_manual_seed_entry(entry: ManualEnzymeEntry) -> List[str]:
    """Validate a single manual seed entry."""

    return _validate_entries([entry])


def validate_manual_seed_records() -> List[str]:
    """Return a list of validation errors for MANUAL_SEED_RECORDS."""

    return _validate_entries(MANUAL_SEED_RECORDS)


def load_dynamic_seed_entries(storage: StoragePaths) -> List[ManualEnzymeEntry]:
    """Load JSON entries produced by automated curation tooling."""

    llm_dir = storage.project_root / "data" / "llm_curation"
    entries: List[ManualEnzymeEntry] = []
    if not llm_dir.exists():
        return entries

    for payload_path in sorted(llm_dir.glob("*.json")):
        try:
            with open(payload_path, "r") as fh:
                payload = json.load(fh)
            if isinstance(payload, dict):
                entries.append(payload)
        except Exception:
            continue
    return entries


def collect_seed_entries(storage: StoragePaths) -> List[ManualEnzymeEntry]:
    """Combine curated manual entries with dynamically generated ones."""

    entries = list(MANUAL_SEED_RECORDS)
    entries.extend(load_dynamic_seed_entries(storage))
    return entries


def validate_all_seed_entries(storage: StoragePaths) -> List[str]:
    """Validate both curated and dynamic entries."""

    return _validate_entries(collect_seed_entries(storage))


def persist_manual_seed_annotations(storage: StoragePaths) -> Path:
    """Persist manual annotations so they participate in downstream merges."""

    all_entries = collect_seed_entries(storage)
    validation_errors = _validate_entries(all_entries)
    if validation_errors:
        bullet_list = "\n - ".join(validation_errors)
        raise ValueError(f"Manual seed validation failed: \n - {bullet_list}")

    annotations_dir = storage.warehouse_dir / "enzyme_annotations"
    annotations_dir.mkdir(parents=True, exist_ok=True)
    output_path = annotations_dir / "manual_seed_annotations.json"

    payload = {
        "source": "manual_seed",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "records": [_normalize_record(entry) for entry in all_entries],
    }

    with open(output_path, "w") as fh:
        json.dump(payload, fh, indent=2)

    return output_path
