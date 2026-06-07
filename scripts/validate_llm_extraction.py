#!/usr/bin/env python3
"""
Validate LLM extraction against known curated data.

This script tests LLM extraction accuracy by comparing results
against known curated enzyme data.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.llm_extraction import LLMEnzymeExtractor
from api_clients import PubMedClient


def load_curated_data(drug_name: str) -> Dict:
    """Load curated data for a drug."""
    curated_file = project_root / "data" / "curated" / f"{drug_name.lower()}.json"
    if not curated_file.exists():
        return {}
    
    with open(curated_file, 'r') as f:
        data = json.load(f)
    
    return data.get("enzyme_data", {})


def compare_extraction_results(llm_result: Dict, curated_data: Dict) -> Dict:
    """
    Compare LLM extraction results with curated data.
    
    Returns comparison metrics.
    """
    comparison = {
        "substrate_match": False,
        "inhibition_match": False,
        "induction_match": False,
        "substrate_tp": 0,  # True positive
        "substrate_fp": 0,  # False positive
        "substrate_fn": 0,  # False negative
        "inhibition_tp": 0,
        "inhibition_fp": 0,
        "inhibition_fn": 0,
        "induction_tp": 0,
        "induction_fp": 0,
        "induction_fn": 0,
        "details": []
    }
    
    # Compare substrate data
    curated_substrates = set(curated_data.get("substrate", {}).keys())
    llm_substrates = set(llm_result.get("substrate", {}).keys())
    
    for enzyme in curated_substrates:
        if enzyme in llm_substrates:
            comparison["substrate_tp"] += 1
            comparison["details"].append(f"✓ Substrate {enzyme} correctly identified")
        else:
            comparison["substrate_fn"] += 1
            comparison["details"].append(f"✗ Substrate {enzyme} missed by LLM")
    
    for enzyme in llm_substrates:
        if enzyme not in curated_substrates:
            comparison["substrate_fp"] += 1
            comparison["details"].append(f"⚠ Substrate {enzyme} incorrectly identified by LLM")
    
    if curated_substrates == llm_substrates:
        comparison["substrate_match"] = True
    
    # Compare inhibition data
    curated_inhibitions = set(curated_data.get("inhibition", {}).keys())
    llm_inhibitions = set(llm_result.get("inhibition", {}).keys())
    
    for enzyme in curated_inhibitions:
        if enzyme in llm_inhibitions:
            comparison["inhibition_tp"] += 1
            comparison["details"].append(f"✓ Inhibition {enzyme} correctly identified")
        else:
            comparison["inhibition_fn"] += 1
            comparison["details"].append(f"✗ Inhibition {enzyme} missed by LLM")
    
    for enzyme in llm_inhibitions:
        if enzyme not in curated_inhibitions:
            comparison["inhibition_fp"] += 1
            comparison["details"].append(f"⚠ Inhibition {enzyme} incorrectly identified by LLM")
    
    if curated_inhibitions == llm_inhibitions:
        comparison["inhibition_match"] = True
    
    # Compare induction data
    curated_inductions = set(curated_data.get("induction", {}).keys())
    llm_inductions = set(llm_result.get("induction", {}).keys())
    
    for enzyme in curated_inductions:
        if enzyme in llm_inductions:
            comparison["induction_tp"] += 1
            comparison["details"].append(f"✓ Induction {enzyme} correctly identified")
        else:
            comparison["induction_fn"] += 1
            comparison["details"].append(f"✗ Induction {enzyme} missed by LLM")
    
    for enzyme in llm_inductions:
        if enzyme not in curated_inductions:
            comparison["induction_fp"] += 1
            comparison["details"].append(f"⚠ Induction {enzyme} incorrectly identified by LLM")
    
    if curated_inductions == llm_inductions:
        comparison["induction_match"] = True
    
    return comparison


def validate_drug(drug_name: str, model: str = "llama3") -> Dict:
    """
    Validate LLM extraction for a single drug against curated data.
    
    Args:
        drug_name: Name of the drug
        model: Ollama model name
    
    Returns:
        Validation results
    """
    print(f"\n{'='*60}")
    print(f"Validating LLM Extraction for {drug_name}")
    print(f"{'='*60}")
    
    # Load curated data
    curated_data = load_curated_data(drug_name)
    if not curated_data:
        print(f"ERROR: No curated data found for {drug_name}")
        return {"error": "No curated data found"}
    
    print(f"\nCurated data:")
    print(f"  Substrates: {list(curated_data.get('substrate', {}).keys())}")
    print(f"  Inhibitions: {list(curated_data.get('inhibition', {}).keys())}")
    print(f"  Inductions: {list(curated_data.get('induction', {}).keys())}")
    
    # Initialize LLM extractor
    try:
        extractor = LLMEnzymeExtractor(model="llama3")
    except Exception as e:
        print(f"ERROR: {e}")
        return {"error": str(e)}
    
    # Search PubMed and extract with LLM
    pubmed = PubMedClient()
    papers = pubmed.search_enzyme_data(drug_name)
    
    if not papers:
        print("ERROR: No PubMed papers found")
        return {"error": "No PubMed papers found"}
    
    print(f"\nFound {len(papers)} PubMed papers")
    print("Processing with LLM...")
    
    # Aggregate LLM extraction results from all papers
    llm_aggregated = {
        "substrate": {},
        "inhibition": {},
        "induction": {}
    }
    
    for i, paper in enumerate(papers[:10], 1):  # Use 10 papers for better coverage
        print(f"  Paper {i}/{min(len(papers), 10)}: {paper['title'][:50]}...")
        
        if not paper['abstract']:
            print("    No abstract available")
            continue
        
        extracted = extractor.extract_from_abstract(paper['abstract'], drug_name)
        
        # Merge substrate data
        for enzyme, data in extracted.get("substrate", {}).items():
            if enzyme not in llm_aggregated["substrate"]:
                llm_aggregated["substrate"][enzyme] = data
        
        # Merge inhibition data
        for enzyme, data in extracted.get("inhibition", {}).items():
            if enzyme not in llm_aggregated["inhibition"]:
                llm_aggregated["inhibition"][enzyme] = data
        
        # Merge induction data
        for enzyme, data in extracted.get("induction", {}).items():
            if enzyme not in llm_aggregated["induction"]:
                llm_aggregated["induction"][enzyme] = data
    
    print(f"\nLLM extracted data:")
    print(f"  Substrates: {list(llm_aggregated['substrate'].keys())}")
    print(f"  Inhibitions: {list(llm_aggregated['inhibition'].keys())}")
    print(f"  Inductions: {list(llm_aggregated['induction'].keys())}")
    
    # Compare results
    comparison = compare_extraction_results(llm_aggregated, curated_data)
    
    # Print comparison
    print(f"\n{'='*60}")
    print("Validation Results")
    print(f"{'='*60}")
    
    for detail in comparison["details"]:
        print(f"  {detail}")
    
    print(f"\nMetrics:")
    print(f"  Substrate match: {comparison['substrate_match']}")
    print(f"    True positives: {comparison['substrate_tp']}")
    print(f"    False positives: {comparison['substrate_fp']}")
    print(f"    False negatives: {comparison['substrate_fn']}")
    print(f"  Inhibition match: {comparison['inhibition_match']}")
    print(f"    True positives: {comparison.get('inhibition_tp', 0)}")
    print(f"    False positives: {comparison.get('inhibition_fp', 0)}")
    print(f"    False negatives: {comparison.get('inhibition_fn', 0)}")
    print(f"  Induction match: {comparison['induction_match']}")
    print(f"    True positives: {comparison.get('induction_tp', 0)}")
    print(f"    False positives: {comparison.get('induction_fp', 0)}")
    print(f"    False negatives: {comparison.get('induction_fn', 0)}")
    
    # Calculate overall accuracy
    total_tp = comparison.get('substrate_tp', 0) + comparison.get('inhibition_tp', 0) + comparison.get('induction_tp', 0)
    total_fp = comparison.get('substrate_fp', 0) + comparison.get('inhibition_fp', 0) + comparison.get('induction_fp', 0)
    total_fn = comparison.get('substrate_fn', 0) + comparison.get('inhibition_fn', 0) + comparison.get('induction_fn', 0)
    
    if total_tp + total_fp + total_fn > 0:
        accuracy = total_tp / (total_tp + total_fp + total_fn)
        print(f"\nOverall accuracy: {accuracy:.2%}")
    
    return {
        "drug_name": drug_name,
        "curated_data": curated_data,
        "llm_extracted": llm_aggregated,
        "comparison": comparison
    }


def main():
    """Main function to run validation."""
    print("="*60)
    print("LLM Extraction Validation")
    print("="*60)
    
    # Test with drugs that have known curated data
    test_drugs = [
        "ketoconazole",  # Known strong CYP3A4 inhibitor
        "midazolam",     # Known CYP3A4 substrate
        "clarithromycin", # Known CYP3A4 inhibitor
    ]
    
    results = []
    for drug in test_drugs:
        result = validate_drug(drug)
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("Validation Summary")
    print(f"{'='*60}")
    
    for result in results:
        if "error" in result:
            print(f"{result['drug_name']}: ERROR - {result['error']}")
        else:
            comp = result['comparison']
            substrate_acc = comp['substrate_tp'] / (comp['substrate_tp'] + comp['substrate_fp'] + comp['substrate_fn']) if (comp['substrate_tp'] + comp['substrate_fp'] + comp['substrate_fn']) > 0 else 0
            inhibition_acc = comp['inhibition_tp'] / (comp['inhibition_tp'] + comp['inhibition_fp'] + comp['inhibition_fn']) if (comp['inhibition_tp'] + comp['inhibition_fp'] + comp['inhibition_fn']) > 0 else 0
            print(f"{result['drug_name']}:")
            print(f"  Substrate accuracy: {substrate_acc:.2%}")
            print(f"  Inhibition accuracy: {inhibition_acc:.2%}")


if __name__ == "__main__":
    main()
