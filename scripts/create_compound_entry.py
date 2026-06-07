#!/usr/bin/env python3
"""
Script to create a new compound entry JSON file from the curation template.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


def create_compound_skeleton(compound_name: str, compound_id: str) -> Dict[str, Any]:
    """
    Create a skeleton compound data structure.
    
    Args:
        compound_name: Name of the compound
        compound_id: Unique identifier for the compound
    
    Returns:
        Dictionary with compound data structure
    """
    enzymes = ["CYP1A2", "CYP2B6", "CYP2C8", "CYP2C9", "CYP2C19", "CYP2D6", "CYP2E1", "CYP3A4", "CYP3A5"]
    
    compound_data = {
        "compound_id": compound_id,
        "compound_name": compound_name,
        "cas_number": "",
        "drugbank_id": "",
        "fda_application_number": "",
        "atc_code": "",
        "therapeutic_class": "",
        "enzyme_data": {
            "substrate": {enzyme: {
                "is_substrate": False,
                "km_um": None,
                "vmax": None,
                "clint": None,
                "fm": None,
                "source": ""
            } for enzyme in enzymes},
            "inhibition": {enzyme: {
                "is_inhibitor": False,
                "inhibition_type": None,
                "ic50_um": None,
                "ki_um": None,
                "source": ""
            } for enzyme in enzymes},
            "induction": {enzyme: {
                "is_inducer": False,
                "induction_type": None,
                "fold_change": None,
                "source": ""
            } for enzyme in enzymes}
        },
        "known_ddis": [],
        "pharmacokinetics": {
            "bioavailability_percent": None,
            "protein_binding_percent": None,
            "vd_lkg": None,
            "clearance_mlminkg": None,
            "half_life_hours": None,
            "major_metabolites": []
        },
        "sources": [],
        "curation_metadata": {
            "curator": "",
            "curation_date": datetime.now().strftime("%Y-%m-%d"),
            "quality_rating": "",
            "peer_reviewer": "",
            "peer_review_date": "",
            "comments": ""
        }
    }
    
    return compound_data


def create_compound_file(compound_name: str, output_dir: Path, compound_id: Optional[str] = None):
    """
    Create a new compound entry JSON file.
    
    Args:
        compound_name: Name of the compound
        output_dir: Directory to save the file
        compound_id: Optional compound ID (defaults to lowercase compound name)
    """
    if compound_id is None:
        compound_id = compound_name.lower().replace(" ", "_")
    
    compound_data = create_compound_skeleton(compound_name, compound_id)
    
    filename = f"{compound_id}.json"
    output_path = output_dir / filename
    
    with open(output_path, 'w') as f:
        json.dump(compound_data, f, indent=2)
    
    print(f"Created compound entry: {output_path}")
    print(f"Compound: {compound_name}")
    print(f"ID: {compound_id}")
    print("\nNext steps:")
    print(f"1. Edit {filename} with compound data")
    print("2. Follow the template in docs/curation_template.md")
    print("3. Run validation: python scripts/validate_data.py")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python create_compound_entry.py <compound_name> [compound_id]")
        print("Example: python create_compound_entry.py Warfarin")
        print("Example: python create_compound_entry.py Warfarin warfarin_sodium")
        sys.exit(1)
    
    compound_name = sys.argv[1]
    compound_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    project_root = Path(__file__).parent.parent
    curated_dir = project_root / "data" / "curated"
    
    if not curated_dir.exists():
        curated_dir.mkdir(parents=True, exist_ok=True)
    
    create_compound_file(compound_name, curated_dir, compound_id)


if __name__ == "__main__":
    main()
