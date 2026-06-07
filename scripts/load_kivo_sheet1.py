#!/usr/bin/env python3
"""
Data loader for Kivo Sheet1 dataset.

Loads the actual compound data from Training Dataset Kivo(Sheet1).csv and converts to JSON format
compatible with our compound schema.
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Optional
import sys


def load_kivo_sheet1(csv_path: Path) -> pd.DataFrame:
    """
    Load Kivo Sheet1 CSV file with proper encoding handling.
    
    Args:
        csv_path: Path to Kivo Sheet1 CSV file
    
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


def kivo_sheet1_to_compound_dict(row: pd.Series) -> Dict:
    """
    Convert a Kivo Sheet1 CSV row to compound dictionary format.
    
    Args:
        row: Pandas Series containing compound data
    
    Returns:
        Dictionary matching our compound schema
    """
    # Initialize enzyme data structure
    enzymes = ["CYP1A2", "CYP2B6", "CYP2C8", "CYP2C9", "CYP2C19", "CYP2D6", "CYP2E1", "CYP3A4", "CYP3A5", "UGT1A1", "UGT2B7"]
    
    enzyme_data = {
        "substrate": {},
        "inhibition": {},
        "induction": {}
    }
    
    # Parse dominant enzyme if available
    dominant_enzyme = row.get('dominant_enzyme', '')
    if dominant_enzyme and pd.notna(dominant_enzyme):
        dominant_enzyme = str(dominant_enzyme).strip()
        enzyme_data["substrate"][dominant_enzyme] = {
            "is_substrate": True,
            "km_um": None,
            "vmax": None,
            "clint": None,
            "fm": row.get('fm_dominant') if pd.notna(row.get('fm_dominant')) else None,
            "source": "Kivo Dataset"
        }
    
    # Parse secondary enzyme if available
    secondary_enzyme = row.get('secondary_enzyme', '')
    if secondary_enzyme and pd.notna(secondary_enzyme):
        secondary_enzyme = str(secondary_enzyme).strip()
        if secondary_enzyme and secondary_enzyme != '':
            enzyme_data["substrate"][secondary_enzyme] = {
                "is_substrate": True,
                "km_um": None,
                "vmax": None,
                "clint": None,
                "fm": None,
                "source": "Kivo Dataset"
            }
    
    # Build compound dictionary
    drug_name = row.get('drug_name', '')
    if not drug_name or pd.isna(drug_name):
        drug_name = f"compound_{row.get('Internal_ID', 'unknown')}"
    
    compound_dict = {
        "compound_id": str(drug_name).lower().replace(' ', '_').replace('-', '_'),
        "compound_name": str(drug_name),
        "cas_number": '',
        "drugbank_id": '',
        "fda_application_number": '',
        "atc_code": '',
        "therapeutic_class": '',
        "smiles": str(row.get('smiles', '')) if pd.notna(row.get('smiles')) else '',
        "inchi_key": str(row.get('inchi_key', '')) if pd.notna(row.get('inchi_key')) else '',
        "molecular_weight_g_mol": row.get('molecular_weight') if pd.notna(row.get('molecular_weight')) else None,
        "logp": row.get('logP') if pd.notna(row.get('logP')) else None,
        "pka": row.get('pKa') if pd.notna(row.get('pKa')) else None,
        "polar_surface_area_a2": row.get('polar_surface_area') if pd.notna(row.get('polar_surface_area')) else None,
        "enzyme_data": enzyme_data,
        "known_ddis": [],
        "pharmacokinetics": {
            "bioavailability_percent": None,
            "protein_binding_percent": None,
            "vd_lkg": None,
            "clearance_mlminkg": None,
            "clearance_l_h": row.get('clearance_L_h_kg') if pd.notna(row.get('clearance_L_h_kg')) else None,
            "half_life_hours": row.get('half_life_h') if pd.notna(row.get('half_life_h')) else None,
            "dose_mg": row.get('dose_mg') if pd.notna(row.get('dose_mg')) else None,
            "auc_ng_h_ml": row.get('AUC_ng_h_ml') if pd.notna(row.get('AUC_ng_h_ml')) else None,
            "cmax_ng_ml": row.get('Cmax_ng_ml') if pd.notna(row.get('Cmax_ng_ml')) else None,
            "major_metabolites": []
        },
        "ddi_studies": [],
        "sources": [],
        "curation_metadata": {
            "curator": str(row.get('Owner', 'Kivo')) if pd.notna(row.get('Owner')) else 'Kivo',
            "curation_date": pd.Timestamp.now().strftime("%Y-%m-%d"),
            "quality_rating": "B",
            "peer_reviewer": "",
            "peer_review_date": "",
            "comments": "Imported from Kivo Sheet1 dataset"
        },
        "metabolism_type": str(row.get('metabolism_type', 'Other')) if pd.notna(row.get('metabolism_type')) else 'Other'
    }
    
    # Parse DDI studies if available
    inhibitor_tested = row.get('inhibitor_tested_SMILES', '')
    enzyme_inhibited = row.get('enzyme_inhibited', '')
    auc_fold_change = row.get('AUC_fold_change', '')
    
    if inhibitor_tested and pd.notna(inhibitor_tested) and str(inhibitor_tested).strip():
        ddi_study = {
            "inhibitor_tested": str(inhibitor_tested),
            "enzyme_inhibited": str(enzyme_inhibited) if pd.notna(enzyme_inhibited) else '',
            "auc_fold_change": float(auc_fold_change) if pd.notna(auc_fold_change) and str(auc_fold_change).strip() else None,
            "cmax_fold_change": None,
            "study_design": "",
            "source": str(row.get('data_source', '')) if pd.notna(row.get('data_source')) else '',
            "notes": ""
        }
        compound_dict["ddi_studies"].append(ddi_study)
        
        # Also add to known_ddis for compatibility
        compound_dict["known_ddis"].append({
            "interacting_drug": str(inhibitor_tested),
            "risk_category": "moderate",
            "clinical_effect": f"AUC fold change: {auc_fold_change}" if pd.notna(auc_fold_change) and str(auc_fold_change).strip() else "",
            "evidence_source": str(row.get('data_source', '')) if pd.notna(row.get('data_source')) else '',
            "notes": ""
        })
    
    # Add source
    data_source = row.get('data_source', '')
    if data_source and pd.notna(data_source):
        compound_dict["sources"].append({
            "source_type": "Kivo Dataset",
            "source_name": str(data_source),
            "url": "",
            "access_date": pd.Timestamp.now().strftime("%Y-%m-%d")
        })
    
    return compound_dict


def convert_kivo_sheet1_to_json(csv_path: Path, output_dir: Path):
    """
    Convert Kivo Sheet1 CSV file to individual JSON files for each compound.
    
    Args:
        csv_path: Path to Kivo Sheet1 CSV file
        output_dir: Directory to save JSON files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load CSV
    df = load_kivo_sheet1(csv_path)
    
    print(f"Loaded {len(df)} rows from CSV")
    
    # Convert each row to compound JSON
    converted_count = 0
    skipped_count = 0
    for idx, row in df.iterrows():
        try:
            drug_name = row.get('drug_name', '')
            if not drug_name or pd.isna(drug_name):
                print(f"Skipping row {idx}: No drug name")
                skipped_count += 1
                continue
            
            compound_dict = kivo_sheet1_to_compound_dict(row)
            
            # Save as JSON
            compound_id = compound_dict["compound_id"]
            output_path = output_dir / f"{compound_id}.json"
            
            with open(output_path, 'w') as f:
                json.dump(compound_dict, f, indent=2)
            
            converted_count += 1
            print(f"Converted: {compound_dict['compound_name']} -> {compound_id}.json")
            
        except Exception as e:
            print(f"Error converting row {idx}: {e}")
            skipped_count += 1
    
    print(f"\nConversion complete: {converted_count}/{len(df)} compounds converted, {skipped_count} skipped")


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    
    # Path to Kivo Sheet1 CSV
    kivo_csv = project_root / "Training Dataset Kivo(Sheet1).csv"
    
    # Output directory
    output_dir = data_dir / "curated"
    
    if not kivo_csv.exists():
        print(f"Kivo Sheet1 CSV not found at: {kivo_csv}")
        print("Please place the Kivo Sheet1 dataset CSV in the project root")
        sys.exit(1)
    
    convert_kivo_sheet1_to_json(kivo_csv, output_dir)


if __name__ == "__main__":
    main()
