#!/usr/bin/env python3
"""
Validate LLM extraction from structured database APIs against curated data.

This script tests the new structured data approach (OpenFDA, ChEMBL, MyChem.info)
against the manually curated enzyme data.
"""

import sys
import json
from pathlib import Path
from typing import Dict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llm_extraction import LLMEnzymeExtractor


def load_curated_data(drug_name: str) -> Dict:
    """Load curated enzyme data for a drug."""
    curated_file = project_root / "data" / "curated" / f"{drug_name.lower()}.json"
    
    if not curated_file.exists():
        print(f"ERROR: Curated data file not found: {curated_file}")
        return None
    
    with open(curated_file, 'r') as f:
        data = json.load(f)
    
    return data.get("enzyme_data", {})


def compare_extraction(extracted: Dict, curated: Dict) -> Dict:
    """Compare extracted data with curated data."""
    results = {
        "substrate": {"tp": 0, "fp": 0, "fn": 0, "matches": [], "false_positives": [], "false_negatives": []},
        "inhibition": {"tp": 0, "fp": 0, "fn": 0, "matches": [], "false_positives": [], "false_negatives": []},
        "induction": {"tp": 0, "fp": 0, "fn": 0, "matches": [], "false_positives": [], "false_negatives": []}
    }
    
    # Compare substrates
    curated_substrates = set(curated.get("substrate", {}).keys())
    extracted_substrates = set(extracted.get("substrate", {}).keys())
    
    for enzyme in extracted_substrates:
        if enzyme in curated_substrates:
            results["substrate"]["tp"] += 1
            results["substrate"]["matches"].append(enzyme)
        else:
            results["substrate"]["fp"] += 1
            results["substrate"]["false_positives"].append(enzyme)
    
    for enzyme in curated_substrates:
        if enzyme not in extracted_substrates:
            results["substrate"]["fn"] += 1
            results["substrate"]["false_negatives"].append(enzyme)
    
    # Compare inhibitions
    curated_inhibitions = set(curated.get("inhibition", {}).keys())
    extracted_inhibitions = set(extracted.get("inhibition", {}).keys())
    
    for enzyme in extracted_inhibitions:
        if enzyme in curated_inhibitions:
            results["inhibition"]["tp"] += 1
            results["inhibition"]["matches"].append(enzyme)
        else:
            results["inhibition"]["fp"] += 1
            results["inhibition"]["false_positives"].append(enzyme)
    
    for enzyme in curated_inhibitions:
        if enzyme not in extracted_inhibitions:
            results["inhibition"]["fn"] += 1
            results["inhibition"]["false_negatives"].append(enzyme)
    
    # Compare inductions
    curated_inductions = set(curated.get("induction", {}).keys())
    extracted_inductions = set(extracted.get("induction", {}).keys())
    
    for enzyme in extracted_inductions:
        if enzyme in curated_inductions:
            results["induction"]["tp"] += 1
            results["induction"]["matches"].append(enzyme)
        else:
            results["induction"]["fp"] += 1
            results["induction"]["false_positives"].append(enzyme)
    
    for enzyme in curated_inductions:
        if enzyme not in extracted_inductions:
            results["induction"]["fn"] += 1
            results["induction"]["false_negatives"].append(enzyme)
    
    return results


def calculate_accuracy(results: Dict) -> Dict:
    """Calculate accuracy metrics."""
    metrics = {}
    
    for category in ["substrate", "inhibition", "induction"]:
        tp = results[category]["tp"]
        fp = results[category]["fp"]
        fn = results[category]["fn"]
        
        total = tp + fp + fn
        if total > 0:
            accuracy = tp / total
        else:
            accuracy = 1.0  # No data to compare = perfect match
        
        metrics[category] = accuracy
    
    return metrics


def validate_structured_llm_extraction_for_drug(drug_name: str) -> Dict:
    """Validate structured LLM extraction for a specific drug."""
    print(f"\n{'='*60}")
    print(f"Validating Structured LLM Extraction for {drug_name}")
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
    
    # Extract with LLM from structured data
    print(f"\nExtracting with LLM from structured databases...")
    extracted_data = extractor.extract_from_structured_data(drug_name)
    
    print(f"\nLLM extracted data:")
    print(f"  Substrates: {list(extracted_data.get('substrate', {}).keys())}")
    print(f"  Inhibitions: {list(extracted_data.get('inhibition', {}).keys())}")
    print(f"  Inductions: {list(extracted_data.get('induction', {}).keys())}")
    
    # Compare with curated data
    print(f"\n{'='*60}")
    print(f"Validation Results")
    print(f"{'='*60}")
    
    comparison = compare_extraction(extracted_data, curated_data)
    metrics = calculate_accuracy(comparison)
    
    # Print results
    for enzyme in comparison["substrate"]["matches"]:
        print(f"  ✓ Substrate {enzyme} correctly identified")
    for enzyme in comparison["substrate"]["false_positives"]:
        print(f"  ⚠ Substrate {enzyme} incorrectly identified by LLM")
    for enzyme in comparison["substrate"]["false_negatives"]:
        print(f"  ✗ Substrate {enzyme} missed by LLM")
    
    for enzyme in comparison["inhibition"]["matches"]:
        print(f"  ✓ Inhibition {enzyme} correctly identified")
    for enzyme in comparison["inhibition"]["false_positives"]:
        print(f"  ⚠ Inhibition {enzyme} incorrectly identified by LLM")
    for enzyme in comparison["inhibition"]["false_negatives"]:
        print(f"  ✗ Inhibition {enzyme} missed by LLM")
    
    for enzyme in comparison["induction"]["matches"]:
        print(f"  ✓ Induction {enzyme} correctly identified")
    for enzyme in comparison["induction"]["false_positives"]:
        print(f"  ⚠ Induction {enzyme} incorrectly identified by LLM")
    for enzyme in comparison["induction"]["false_negatives"]:
        print(f"  ✗ Induction {enzyme} missed by LLM")
    
    # Print metrics
    print(f"\nMetrics:")
    print(f"  Substrate match: {metrics['substrate'] == 1.0}")
    print(f"    True positives: {comparison['substrate']['tp']}")
    print(f"    False positives: {comparison['substrate']['fp']}")
    print(f"    False negatives: {comparison['substrate']['fn']}")
    print(f"  Inhibition match: {metrics['inhibition'] == 1.0}")
    print(f"    True positives: {comparison['inhibition']['tp']}")
    print(f"    False positives: {comparison['inhibition']['fp']}")
    print(f"    False negatives: {comparison['inhibition']['fn']}")
    print(f"  Induction match: {metrics['induction'] == 1.0}")
    print(f"    True positives: {comparison['induction']['tp']}")
    print(f"    False positives: {comparison['induction']['fp']}")
    print(f"    False negatives: {comparison['induction']['fn']}")
    
    # Calculate overall accuracy
    overall_accuracy = sum(metrics.values()) / len(metrics) * 100
    print(f"\nOverall accuracy: {overall_accuracy:.2f}%")
    
    return {
        "extracted": extracted_data,
        "curated": curated_data,
        "comparison": comparison,
        "metrics": metrics,
        "overall_accuracy": overall_accuracy
    }


def main():
    """Main function to validate structured LLM extraction."""
    print("="*60)
    print("Structured LLM Extraction Validation")
    print("="*60)
    
    # Test with curated drugs
    test_drugs = ["ketoconazole", "midazolam", "clarithromycin"]
    
    all_results = {}
    for drug in test_drugs:
        result = validate_structured_llm_extraction_for_drug(drug)
        all_results[drug] = result
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Validation Summary")
    print(f"{'='*60}")
    
    for drug, result in all_results.items():
        if "error" not in result:
            metrics = result["metrics"]
            substrate_acc = metrics["substrate"] * 100
            inhibition_acc = metrics["inhibition"] * 100
            induction_acc = metrics["induction"] * 100
            
            print(f"{drug}:")
            print(f"  Substrate accuracy: {substrate_acc:.2f}%")
            print(f"  Inhibition accuracy: {inhibition_acc:.2f}%")
            print(f"  Induction accuracy: {induction_acc:.2f}%")
            print(f"  Overall accuracy: {result['overall_accuracy']:.2f}%")


if __name__ == "__main__":
    main()
