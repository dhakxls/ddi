#!/usr/bin/env python3
"""
Data loader for Kivo dataset format.

Loads PK data from CSV files following the Kivo schema and converts to JSON format
compatible with our compound schema.
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Optional
import sys


def load_kivo_csv(csv_path: Path) -> pd.DataFrame:
    """
    Load Kivo CSV file with proper encoding handling.
    
    Args:
        csv_path: Path to Kivo CSV file
    
    Returns:
        DataFrame with Kivo data
    """
    # Try different encodings
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(csv_path, encoding=encoding)
            print(f"Successfully loaded with encoding: {encoding}")
            return df
        except Exception as e:
            print(f"Failed with encoding {encoding}: {e}")
            continue
    
    raise ValueError(f"Could not load CSV file {csv_path} with any encoding")


def kivo_to_compound_dict(row: pd.Series) -> Dict:
    """
    Convert a Kivo CSV row to compound dictionary format.
    
    Args:
        row: Pandas Series containing compound data
    
    Returns:
        Dictionary matching our compound schema
    """
    # Initialize enzyme data structure
    enzymes = ["CYP1A2", "CYP2B6", "CYP2C8", "CYP2C9", "CYP2C19", "CYP2D6", "CYP2E1", "CYP3A4", "CYP3A5"]
    
    enzyme_data = {
        "substrate": {},
        "inhibition": {},
        "induction": {}
    }
    
    # Parse dominant enzyme if available
    dominant_enzyme = row.get('dominant_enzyme', '')
    if dominant_enzyme and pd.notna(dominant_enzyme):
        dominant_enzyme = str(dominant_enzyme).strip()
        if dominant_enzyme in enzymes:
            enzyme_data["substrate"][dominant_enzyme] = {
                "is_substrate": True,
                "km_um": None,
                "vmax": None,
                "clint": None,
                "fm": row.get('fm_dominant'),
                "source": "FDA Clinical Pharmacology Review"
            }
    
    # Parse secondary enzyme if available
    secondary_enzyme = row.get('secondary_enzyme', '')
    if secondary_enzyme and pd.notna(secondary_enzyme):
        secondary_enzyme = str(secondary_enzyme).strip()
        if secondary_enzyme in enzymes:
            enzyme_data["substrate"][secondary_enzyme] = {
                "is_substrate": True,
                "km_um": None,
                "vmax": None,
                "clint": None,
                "fm": None,  # fm not typically reported for secondary
                "source": "FDA Clinical Pharmacology Review"
            }
    
    # Build compound dictionary
    compound_dict = {
        "compound_id": str(row.get('compound_name', 'unknown')).lower().replace(' ', '_'),
        "compound_name": row.get('compound_name', ''),
        "cas_number": row.get('cas_number', ''),
        "drugbank_id": row.get('drugbank_id', ''),
        "fda_application_number": row.get('fda_application_number', ''),
        "atc_code": row.get('atc_code', ''),
        "therapeutic_class": row.get('therapeutic_class', ''),
        "smiles": row.get('smiles', ''),
        "inchi_key": row.get('inchi_key', ''),
        "molecular_weight_g_mol": row.get('molecular_weight_g_mol'),
        "logp": row.get('logp'),
        "pka": row.get('pka'),
        "polar_surface_area_a2": row.get('polar_surface_area_A2'),
        "enzyme_data": enzyme_data,
        "known_ddis": [],  # Will be populated from DDI studies
        "pharmacokinetics": {
            "bioavailability_percent": None,
            "protein_binding_percent": None,
            "vd_lkg": None,
            "clearance_mlminkg": None,
            "clearance_l_h": row.get('clearance_L_h'),
            "half_life_hours": row.get('half_life_h'),
            "dose_mg": row.get('dose_mg'),
            "auc_ng_h_ml": row.get('AUC_ng_h_ml'),
            "cmax_ng_ml": row.get('Cmax_ng_ml'),
            "major_metabolites": []
        },
        "ddi_studies": [],
        "sources": [],
        "curation_metadata": {
            "curator": "Kivo Dataset Import",
            "curation_date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "quality_rating": "B",  # Default for imported data
            "peer_reviewer": "",
            "peer_review_date": "",
            "comments": "Imported from Kivo dataset format"
        },
        "metabolism_type": row.get('metabolism_type', 'Other')
    }
    
    # Parse DDI studies if available
    inhibitor_tested = row.get('inhibitor_tested', '')
    enzyme_inhibited = row.get('enzyme_inhibited', '')
    auc_fold_change = row.get('AUC_fold_change', '')
    
    if inhibitor_tested and pd.notna(inhibitor_tested) and enzyme_inhibited and pd.notna(enzyme_inhibited):
        ddi_study = {
            "inhibitor_tested": str(inhibitor_tested),
            "enzyme_inhibited": str(enzyme_inhibited),
            "auc_fold_change": auc_fold_change if pd.notna(auc_fold_change) else None,
            "cmax_fold_change": None,
            "study_design": "",
            "source": row.get('data_source', ''),
            "notes": ""
        }
        compound_dict["ddi_studies"].append(ddi_study)
        
        # Also add to known_ddis for compatibility
        compound_dict["known_ddis"].append({
            "interacting_drug": str(inhibitor_tested),
            "risk_category": "moderate",  # Default category
            "clinical_effect": f"AUC fold change: {auc_fold_change}" if pd.notna(auc_fold_change) else "",
            "evidence_source": row.get('data_source', ''),
            "notes": ""
        })
    
    # Add source
    data_source = row.get('data_source', '')
    if data_source and pd.notna(data_source):
        compound_dict["sources"].append({
            "source_type": "Other",
            "source_name": str(data_source),
            "url": "",
            "access_date": pd.Timestamp.now().strftime("%Y-%m-%d")
        })
    
    return compound_dict


def convert_kivo_to_json(csv_path: Path, output_dir: Path):
    """
    Convert Kivo CSV file to individual JSON files for each compound.
    
    Args:
        csv_path: Path to Kivo CSV file
        output_dir: Directory to save JSON files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load CSV
    df = load_kivo_csv(csv_path)
    
    print(f"Loaded {len(df)} rows from CSV")
    
    # Check if this is a template file (has column descriptions in first rows)
    if df.iloc[0, 0] == 'assume 70KG MALE':
        print("Detected template file - no data rows to convert")
        print("This appears to be a schema/template file, not actual data")
        return
    
    # Convert each row to compound JSON
    converted_count = 0
    for idx, row in df.iterrows():
        try:
            compound_dict = kivo_to_compound_dict(row)
            
            # Save as JSON
            compound_id = compound_dict["compound_id"]
            output_path = output_dir / f"{compound_id}.json"
            
            with open(output_path, 'w') as f:
                json.dump(compound_dict, f, indent=2)
            
            converted_count += 1
            print(f"Converted: {compound_dict['compound_name']} -> {compound_id}.json")
            
        except Exception as e:
            print(f"Error converting row {idx}: {e}")
    
    print(f"\nConversion complete: {converted_count}/{len(df)} compounds converted")


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    
    # Path to Kivo CSV
    kivo_csv = project_root / "Training Dataset Kivo(READ ME).csv"
    
    # Output directory
    output_dir = data_dir / "curated"
    
    if not kivo_csv.exists():
        print(f"Kivo CSV not found at: {kivo_csv}")
        print("Please place the Kivo dataset CSV in the project root")
        sys.exit(1)
    
    convert_kivo_to_json(kivo_csv, output_dir)


if __name__ == "__main__":
    main()
