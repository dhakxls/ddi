#!/usr/bin/env python3
"""
Update Compound Data with API-derived and manually curated values.

This script:
1. Fetches SMILES and MW from PubChem API (dynamic - works for any drug)
2. Detects enzyme mentions from OpenFDA (dynamic - works for any drug)
3. Adds manually curated fm data (not dynamic - requires literature search)
4. Handles missing fm data gracefully for novel drugs

For novel/unstudied drugs:
- Chemical properties (SMILES, MW): Can be fetched dynamically
- Enzyme mentions: Can be detected dynamically
- fm data: Not available - requires manual curation or ML prediction
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import api_clients
sys.path.append(str(Path(__file__).parent.parent))

from api_clients import DataMerger

# NOTE: Manual fm data removed - all data must have documented sources
# Future fm values must be added with proper literature citations


def update_compound_json(compound_name: str, json_path: str):
    """
    Update a single compound JSON file with API-derived data.
    
    Note: fm data is NOT added automatically - must be manually curated with documented sources.
    
    Args:
        compound_name: Name of the compound
        json_path: Path to the JSON file
    """
    print(f"\nUpdating {compound_name}...")
    
    # Load existing JSON
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Fetch API data (dynamic - works for any drug)
    merger = DataMerger()
    api_data = merger.get_consolidated_drug_data(compound_name)
    
    # Update SMILES if missing or from API
    if api_data.smiles and (not data.get("smiles") or data.get("smiles") == ""):
        data["smiles"] = api_data.smiles
        print(f"  ✓ Updated SMILES: {api_data.smiles}")
    
    # Update molecular weight if missing or from API
    if api_data.molecular_weight and (not data.get("molecular_weight_g_mol") or data.get("molecular_weight_g_mol") == 0):
        data["molecular_weight_g_mol"] = api_data.molecular_weight
        print(f"  ✓ Updated MW: {api_data.molecular_weight}")
    
    # Update enzyme data with API-detected mentions
    if api_data.enzyme_data:
        for enzyme, enzyme_info in api_data.enzyme_data.items():
            if enzyme not in data["enzyme_data"]["substrate"]:
                data["enzyme_data"]["substrate"][enzyme] = {
                    "is_substrate": True,
                    "km_um": None,
                    "vmax": None,
                    "clint": None,
                    "fm": None,
                    "source": "OpenFDA API"
                }
        print(f"  ✓ Updated enzyme mentions: {list(api_data.enzyme_data.keys())}")
    
    # NOTE: fm data requires manual curation with documented sources
    # No fm data is added automatically - all values must be sourced
    
    # Update sources metadata
    sources = data.get("sources", [])
    if "PubChem" in api_data.sources and "PubChem" not in sources:
        sources.append("PubChem")
    if "OpenFDA" in api_data.sources and "OpenFDA" not in sources:
        sources.append("OpenFDA")
    data["sources"] = sources
    
    # Save updated JSON
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"  ✓ Saved updated JSON")


def update_all_compounds(data_dir: str):
    """
    Update all compound JSON files in a directory.
    
    Args:
        data_dir: Directory containing compound JSON files
    """
    data_path = Path(data_dir)
    json_files = list(data_path.glob("*.json"))
    
    print("="*60)
    print("Updating Compound Data")
    print("="*60)
    print(f"\nFound {len(json_files)} compound files")
    
    updated_count = 0
    smiles_updated = 0
    mw_updated = 0
    fm_updated = 0
    
    for json_file in json_files:
        compound_name = json_file.stem  # filename without .json
        compound_name_capitalized = compound_name.capitalize()
        
        try:
            old_smiles = None
            old_mw = None
            old_fm = None
            
            # Check what's being updated
            with open(json_file, 'r') as f:
                old_data = json.load(f)
                old_smiles = old_data.get("smiles")
                old_mw = old_data.get("molecular_weight_g_mol")
                old_fm = old_data.get("enzyme_data", {}).get("substrate", {}).get("CYP3A4", {}).get("fm")  # Check one enzyme
            
            update_compound_json(compound_name_capitalized, json_file)
            
            # Check what was updated
            with open(json_file, 'r') as f:
                new_data = json.load(f)
                if new_data.get("smiles") != old_smiles and new_data.get("smiles"):
                    smiles_updated += 1
                if new_data.get("molecular_weight_g_mol") != old_mw and new_data.get("molecular_weight_g_mol"):
                    mw_updated += 1
                if compound_name_capitalized in MANUAL_FM_DATA:
                    fm_updated += 1
            
            updated_count += 1
            
        except Exception as e:
            print(f"  ✗ Error updating {compound_name}: {e}")
    
    print("\n" + "="*60)
    print("Update Complete - Summary")
    print("="*60)
    print(f"\nFiles updated: {updated_count}/{len(json_files)}")
    print(f"  SMILES updated: {smiles_updated}")
    print(f"  MW updated: {mw_updated}")
    print(f"  fm data added: {fm_updated}")
    print(f"\nNote: fm data is only available for manually curated compounds.")
    print(f"For novel drugs, fm data requires manual curation or ML prediction.")


if __name__ == "__main__":
    data_dir = "/Users/martinvo/Library/CloudStorage/GoogleDrive-bvomartin@gmail.com/My Drive/DrugData/CascadeProjects/windsurf-project/data/curated"
    update_all_compounds(data_dir)
