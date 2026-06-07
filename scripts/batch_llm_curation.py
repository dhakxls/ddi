#!/usr/bin/env python3
"""
Batch curation of Kivo dataset using LLM extraction from PubMed.

This script processes all 100 compounds from the Kivo dataset
using Ollama LLM for automated enzyme data extraction.
"""

import sys
import json
import csv
from pathlib import Path
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api_clients import PubMedClient
from curate_from_pubmed import EnzymeDataExtractor


def load_kivo_dataset() -> List[str]:
    """
    Load compound names from Kivo dataset.
    
    Returns:
        List of compound names
    """
    csv_file = project_root / "Training Dataset Kivo(Sheet1).csv"
    
    if not csv_file.exists():
        print(f"ERROR: Kivo dataset not found at {csv_file}")
        return []
    
    compounds = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                compound_name = row.get('drug_name')
                if compound_name:
                    compounds.append(compound_name)
    except Exception as e:
        print(f"ERROR reading CSV: {e}")
        return []
    
    return compounds


def batch_curate_kivo_dataset(max_papers: int = 5, start_index: int = 0, end_index: int = None):
    """
    Batch curate Kivo dataset using LLM extraction.
    
    Args:
        model: Ollama model name
        max_papers: Maximum papers per compound
        start_index: Starting index in compound list
        end_index: Ending index in compound list (None for all)
    """
    print("="*60)
    print("Batch LLM Curation of Kivo Dataset")
    print("="*60)
    
    # Load compounds
    compounds = load_kivo_dataset()
    
    if not compounds:
        print("ERROR: No compounds found in Kivo dataset")
        return
    
    print(f"Found {len(compounds)} compounds in Kivo dataset")
    
    # Slice compound list
    if end_index is None:
        end_index = len(compounds)
    compounds = compounds[start_index:end_index]
    
    print(f"Processing compounds {start_index} to {end_index-1} ({len(compounds)} compounds)")
    print(f"Using pattern matching extraction")
    print(f"Max papers per compound: {max_papers}")
    
    # Initialize clients
    try:
        pubmed = PubMedClient()
        extractor = EnzymeDataExtractor()
    except Exception as e:
        print(f"ERROR: {e}")
        return
    
    # Process each compound
    results = {}
    success_count = 0
    failure_count = 0
    
    for i, compound in enumerate(compounds, start=start_index):
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(compounds)+start_index}] Processing: {compound}")
        print(f"{'='*60}")
        
        try:
            # Search for papers
            print(f"Searching PubMed...")
            papers = pubmed.search_enzyme_data(compound)
            
            if not papers:
                print(f"  No papers found for {compound}")
                results[compound] = {"status": "no_papers", "data": {}}
                failure_count += 1
                continue
            
            print(f"  Found {len(papers)} papers")
            print(f"  Processing with pattern matching (max {max_papers} papers)...")
            
            # Extract data from papers
            compound_data = {
                "substrate": {},
                "inhibition": {},
                "induction": {},
                "papers": []
            }
            
            for paper in papers[:max_papers]:
                if not paper['abstract']:
                    continue
                
                # Extract with pattern matching
                extracted = extractor.extract_from_abstract(paper['abstract'])
                
                # Merge data
                for enzyme, data in extracted.get("substrate", {}).items():
                    if enzyme not in compound_data["substrate"]:
                        compound_data["substrate"][enzyme] = data
                    else:
                        # Keep the data with fm value if available
                        if data.get("fm") and not compound_data["substrate"][enzyme].get("fm"):
                            compound_data["substrate"][enzyme] = data
                
                for enzyme, data in extracted.get("inhibition", {}).items():
                    if enzyme not in compound_data["inhibition"]:
                        compound_data["inhibition"][enzyme] = data
                    else:
                        # Keep the stronger inhibition
                        current_type = compound_data["inhibition"][enzyme].get("inhibition_type", "weak")
                        new_type = data.get("inhibition_type", "weak")
                        if new_type in ["strong", "moderate"] and current_type == "weak":
                            compound_data["inhibition"][enzyme] = data
                
                for enzyme, data in extracted.get("induction", {}).items():
                    if enzyme not in compound_data["induction"]:
                        compound_data["induction"][enzyme] = data
                
                # Store paper info
                compound_data["papers"].append({
                    "pmid": paper["pmid"],
                    "title": paper["title"],
                    "journal": paper["journal"],
                    "year": paper["year"]
                })
            
            # Summary for this compound
            substrate_count = len(compound_data["substrate"])
            inhibition_count = len(compound_data["inhibition"])
            induction_count = len(compound_data["induction"])
            
            print(f"  Substrate enzymes: {substrate_count}")
            print(f"  Inhibition enzymes: {inhibition_count}")
            print(f"  Induction enzymes: {induction_count}")
            
            results[compound] = {
                "status": "success",
                "data": compound_data
            }
            success_count += 1
            
        except Exception as e:
            print(f"  ERROR: {e}")
            results[compound] = {"status": "error", "error": str(e)}
            failure_count += 1
    
    # Save batch results
    output_file = project_root / "data" / "llm_curation" / "batch_results.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    print(f"\n{'='*60}")
    print("Batch Curation Summary")
    print(f"{'='*60}")
    print(f"Total compounds: {len(compounds)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    print(f"\nResults saved to: {output_file}")
    print("\nNext steps:")
    print("1. Review extracted data in batch_results.json")
    print("2. Validate high-confidence extractions")
    print("3. Add validated data to curated JSON files")


def main():
    """Main function to run batch curation."""
    # Process first 10 compounds (test run)
    batch_curate_kivo_dataset(max_papers=5, start_index=0, end_index=10)
    
    # To process all 100 compounds, change end_index to None or 100
    # batch_curate_kivo_dataset(model="llama2", max_papers=5, start_index=0, end_index=100)


if __name__ == "__main__":
    main()
