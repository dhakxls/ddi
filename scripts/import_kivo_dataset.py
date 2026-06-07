#!/usr/bin/env python3
"""
Import Kivo Sheet1 dataset and convert to JSON format.

This script:
1. Reads the Kivo Sheet1 CSV file (100 compounds)
2. Converts each row to the JSON format used by the DDI system
3. Saves JSON files to data/curated/ directory
"""

import csv
import json
import os
from pathlib import Path
from typing import Dict, Optional

# CSV file path
KIVO_CSV = "/Users/martinvo/Library/CloudStorage/GoogleDrive-bvomartin@gmail.com/My Drive/DrugData/CascadeProjects/windsurf-project/Training Dataset Kivo(Sheet1).csv"

# Output directory
OUTPUT_DIR = "/Users/martinvo/Library/CloudStorage/GoogleDrive-bvomartin@gmail.com/My Drive/DrugData/CascadeProjects/windsurf-project/data/curated"


def parse_enzyme_data(dominant_enzyme: str, secondary_enzyme: str) -> Dict:
    """
    Parse enzyme data from Kivo format to system format.
    
    Args:
        dominant_enzyme: Dominant enzyme string (e.g., "CYP3A4")
        secondary_enzyme: Secondary enzyme string (e.g., "CYP2D6")
    
    Returns:
        Dictionary with substrate, inhibition, induction data
    """
    enzyme_data = {
        "substrate": {},
        "inhibition": {},
        "induction": {}
    }
    
    # Add dominant enzyme as substrate
    if dominant_enzyme and dominant_enzyme != "Renal" and dominant_enzyme != "Transporter" and dominant_enzyme != "UGT":
        enzyme_data["substrate"][dominant_enzyme] = {
            "is_substrate": True,
            "km_um": None,
            "vmax": None,
            "clint": None,
            "fm": None,  # Will be None unless sourced
            "source": "Kivo dataset"
        }
    
    # Add secondary enzyme if present
    if secondary_enzyme and secondary_enzyme != "None" and secondary_enzyme != "":
        enzyme_data["substrate"][secondary_enzyme] = {
            "is_substrate": True,
            "km_um": None,
            "vmax": None,
            "clint": None,
            "fm": None,
            "source": "Kivo dataset"
        }
    
    return enzyme_data


def convert_row_to_json(row: Dict[str, str]) -> Dict:
    """
    Convert a Kivo CSV row to the system JSON format.
    
    Args:
        row: Dictionary from CSV reader
    
    Returns:
        Dictionary in system JSON format
    """
    drug_name = row.get("drug_name", "").strip()
    if not drug_name:
        return None
    
    # Parse metabolism type
    metabolism_type = row.get("metabolism_type", "").strip()
    if not metabolism_type:
        metabolism_type = "Other"
    
    # Parse enzyme data
    dominant_enzyme = row.get("dominant_enzyme", "").strip()
    secondary_enzyme = row.get("secondary_enzyme", "").strip()
    enzyme_data = parse_enzyme_data(dominant_enzyme, secondary_enzyme)
    
    # Parse numeric fields
    def safe_float(value: str) -> Optional[float]:
        try:
            return float(value) if value and value != "" else None
        except:
            return None
    
    molecular_weight = safe_float(row.get("molecular_weight"))
    logp = safe_float(row.get("logP"))
    pka = safe_float(row.get("pKa"))
    psa = safe_float(row.get("polar_surface_area"))
    
    # Parse PK parameters
    dose_mg = safe_float(row.get("dose_mg"))
    auc = safe_float(row.get("AUC_ng_h_ml"))
    cmax = safe_float(row.get("Cmax_ng_ml"))
    clearance = safe_float(row.get("clearance_L_h_kg"))
    half_life = safe_float(row.get("half_life_h"))
    
    # Build JSON structure
    compound_data = {
        "compound_id": drug_name.lower().replace(" ", "_"),
        "compound_name": drug_name,
        "cas_number": "",
        "drugbank_id": "",
        "fda_application_number": "",
        "atc_code": "",
        "therapeutic_class": "",
        "smiles": row.get("smiles", "").strip(),
        "inchi_key": row.get("inchi_key", "").strip(),
        "molecular_weight_g_mol": molecular_weight,
        "logp": logp,
        "pka": pka,
        "polar_surface_area_a2": psa,
        "enzyme_data": enzyme_data,
        "known_ddis": [],
        "pharmacokinetics": {
            "bioavailability_percent": None,
            "protein_binding_percent": None,
            "vd_lkg": None,
            "clearance_mlminkg": None,
            "clearance_l_h": None,  # Note: Kivo has clearance_L_h_kg, need to convert if weight known
            "half_life_hours": half_life,
            "dose_mg": dose_mg,
            "auc_ng_h_ml": auc,
            "cmax_ng_ml": cmax,
            "major_metabolites": []
        },
        "ddi_studies": [],
        "sources": ["Kivo dataset"],
        "curation_metadata": {
            "curator": row.get("Owner", "").strip(),
            "curation_date": "2026-05-20",
            "quality_rating": "B",
            "peer_reviewer": "",
            "peer_review_date": "",
            "comments": f"Imported from Kivo Sheet1 dataset. Dominant enzyme: {dominant_enzyme}"
        },
        "metabolism_type": metabolism_type
    }
    
    return compound_data


def import_kivo_dataset():
    """
    Import Kivo Sheet1 dataset and convert to JSON files.
    Preserves existing enzyme data (inhibition/induction) from curated files.
    """
    print("="*60)
    print("Importing Kivo Sheet1 Dataset")
    print("="*60)
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Read CSV
    with open(KIVO_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"\nFound {len(rows)} rows in Kivo dataset")
    
    imported_count = 0
    skipped_count = 0
    preserved_count = 0
    
    for row in rows:
        drug_name = row.get("drug_name", "").strip()
        if not drug_name:
            skipped_count += 1
            continue
        
        # Convert to JSON format
        compound_data = convert_row_to_json(row)
        
        if not compound_data:
            skipped_count += 1
            continue
        
        # Check if file already exists
        output_file = os.path.join(OUTPUT_DIR, f"{compound_data['compound_id']}.json")
        
        if os.path.exists(output_file):
            # Load existing data to preserve inhibition/induction
            with open(output_file, 'r') as f:
                existing_data = json.load(f)
            
            # Preserve existing enzyme data (inhibition, induction)
            if "enzyme_data" in existing_data:
                compound_data["enzyme_data"]["inhibition"] = existing_data["enzyme_data"].get("inhibition", {})
                compound_data["enzyme_data"]["induction"] = existing_data["enzyme_data"].get("induction", {})
                preserved_count += 1
            
            # Preserve other fields if they exist and are more complete
            if existing_data.get("pharmacokinetics"):
                for key, value in existing_data["pharmacokinetics"].items():
                    if value is not None and compound_data["pharmacokinetics"].get(key) is None:
                        compound_data["pharmacokinetics"][key] = value
        
        # Save to JSON file
        with open(output_file, 'w') as f:
            json.dump(compound_data, f, indent=2)
        
        imported_count += 1
        status = " (preserved enzyme data)" if os.path.exists(output_file) and preserved_count > 0 else ""
        print(f"  ✓ Imported: {drug_name}{status}")
    
    print("\n" + "="*60)
    print("Import Complete")
    print("="*60)
    print(f"Imported: {imported_count} compounds")
    print(f"Skipped: {skipped_count} compounds")
    print(f"Preserved enzyme data: {preserved_count} compounds")
    print(f"Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    import_kivo_dataset()
