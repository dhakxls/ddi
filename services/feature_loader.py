"""Utilities for loading curated compound data and derived features."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Optional


@dataclass
class CompoundRecord:
    compound_id: str
    data: Dict

    @property
    def features(self) -> Dict:
        enzyme_data = self.data.get("enzyme_data", {})
        pk = self.data.get("pharmacokinetics", {})
        return {
            "compound_name": self.data.get("compound_name"),
            "molecular_weight_g_mol": self.data.get("molecular_weight_g_mol"),
            "logp": self.data.get("logp"),
            "pka": self.data.get("pka"),
            "polar_surface_area_a2": self.data.get("polar_surface_area_a2"),
            "enzyme_counts": {
                "substrate": len(enzyme_data.get("substrate", {})),
                "inhibition": len(enzyme_data.get("inhibition", {})),
                "induction": len(enzyme_data.get("induction", {})),
            },
            "dominant_enzymes": [
                enzyme
                for enzyme, payload in enzyme_data.get("substrate", {}).items()
                if payload.get("fm", 0) and payload.get("fm") >= 0.25
            ],
            "pk": pk,
        }


class CompoundStore:
    def __init__(self, curated_dir: Path):
        self.curated_dir = curated_dir

    def list_compounds(self) -> Dict[str, Path]:
        mapping: Dict[str, Path] = {}
        for json_file in self.curated_dir.glob("*.json"):
            mapping[json_file.stem] = json_file
        return mapping

    @lru_cache(maxsize=256)
    def load_compound(self, compound_id: str) -> Optional[CompoundRecord]:
        compound_path = self.curated_dir / f"{compound_id}.json"
        if not compound_path.exists():
            return None
        with open(compound_path, "r") as handle:
            data = json.load(handle)
        return CompoundRecord(compound_id=compound_id, data=data)
