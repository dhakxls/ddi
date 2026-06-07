#!/usr/bin/env python3
"""
Comprehensive demo with multiple DDI scenarios.

This script demonstrates the DDI prediction tool with various
drug-drug interaction scenarios relevant to clinical trials.
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models.ddi_ranking.ddi_risk_model import DDIRiskRanker


def load_compound(compound_id: str) -> dict:
    """Load compound data from curated directory."""
    curated_dir = project_root / "data" / "curated"
    compound_file = curated_dir / f"{compound_id}.json"
    
    if not compound_file.exists():
        raise FileNotFoundError(f"Compound file not found: {compound_file}")
    
    with open(compound_file, 'r') as f:
        return json.load(f)


def run_ddi_prediction(drug_a: dict, drug_b: dict) -> dict:
    """Run DDI prediction for a drug pair."""
    ranker = DDIRiskRanker()
    result = ranker.rank_drug_pair(drug_a, drug_b)
    return result


def print_scenario_header(title: str):
    """Print scenario header."""
    print(f"\n{'='*60}")
    print(f"SCENARIO: {title}")
    print(f"{'='*60}")


def print_ddi_result(drug_a_name: str, drug_b_name: str, result: dict):
    """Print DDI prediction result."""
    print(f"\nDrug Pair: {drug_a_name} + {drug_b_name}")
    print(f"Risk Category: {result.risk_category.value.upper()}")
    print(f"Risk Score: {result.risk_score:.2f}/100")
    print(f"Mechanism: {result.mechanism.value}")
    print(f"Affected Enzymes: {result.affected_enzymes}")
    print(f"Confidence: {result.confidence}")
    
    print(f"\nClinical Implications:")
    for imp in result.clinical_implications:
        print(f"  - {imp}")
    
    print(f"\nRecommended Actions:")
    for action in result.recommended_actions:
        print(f"  - {action}")


def main():
    """Run comprehensive demo with multiple scenarios."""
    print("="*60)
    print("DDI Prediction MVP - Comprehensive Demo")
    print("="*60)
    print("\nDemonstrating various DDI scenarios relevant to clinical trials")
    
    scenarios = [
        {
            "title": "Major CYP3A4 Inhibition",
            "drug_a": "midazolam",
            "drug_b": "ketoconazole",
            "description": "Benzodiazepine + Strong CYP3A4 inhibitor"
        },
        {
            "title": "CYP2D6 Substrate + Inhibitor",
            "drug_a": "metoprolol",
            "drug_b": "fluoxetine",
            "description": "Beta-blocker + SSRI (CYP2D6 inhibitor)"
        },
        {
            "title": "CYP2C9 Substrate + Inhibitor",
            "drug_a": "warfarin",
            "drug_b": "fluconazole",
            "description": "Anticoagulant + Azole antifungal"
        },
        {
            "title": "Multiple Enzyme Substrate",
            "drug_a": "amiodarone",
            "drug_b": "simvastatin",
            "description": "Antiarrhythmic + Statin (complex DDI potential)"
        },
        {
            "title": "CYP3A4 Induction",
            "drug_a": "midazolam",
            "drug_b": "rifampin",
            "description": "Benzodiazepine + Strong CYP3A4 inducer"
        }
    ]
    
    results_summary = []
    
    for scenario in scenarios:
        print_scenario_header(scenario["title"])
        print(f"Description: {scenario['description']}")
        
        try:
            drug_a = load_compound(scenario["drug_a"])
            drug_b = load_compound(scenario["drug_b"])
            
            result = run_ddi_prediction(drug_a, drug_b)
            print_ddi_result(drug_a["compound_name"], drug_b["compound_name"], result)
            
            results_summary.append({
                "scenario": scenario["title"],
                "drug_pair": f"{drug_a['compound_name']} + {drug_b['compound_name']}",
                "risk_category": result.risk_category.value,
                "risk_score": result.risk_score,
                "mechanism": result.mechanism.value
            })
            
        except FileNotFoundError as e:
            print(f"\nSkipping scenario: {e}")
            print("(Compound not in Kivo dataset)")
        except Exception as e:
            print(f"\nError in scenario: {e}")
    
    # Print summary
    print(f"\n{'='*60}")
    print("DEMO SUMMARY")
    print(f"{'='*60}")
    print(f"\nTotal Scenarios Tested: {len(results_summary)}")
    print(f"\nResults:")
    
    risk_counts = {"major": 0, "moderate": 0, "minor": 0, "unknown": 0}
    
    for i, result in enumerate(results_summary, 1):
        print(f"\n{i}. {result['scenario']}")
        print(f"   Drugs: {result['drug_pair']}")
        print(f"   Risk: {result['risk_category'].upper()} ({result['risk_score']:.1f})")
        print(f"   Mechanism: {result['mechanism']}")
        
        risk_counts[result['risk_category']] += 1
    
    print(f"\n{'='*60}")
    print("Risk Category Distribution:")
    print(f"{'='*60}")
    for category, count in risk_counts.items():
        if count > 0:
            print(f"  {category.upper()}: {count}")
    
    print(f"\n{'='*60}")
    print("Demo Complete")
    print(f"{'='*60}")
    print("\nKey Capabilities Demonstrated:")
    print("  ✓ DDI risk ranking for multiple enzyme systems")
    print("  ✓ Identification of inhibition mechanisms")
    print("  ✓ Clinical implication generation")
    print("  ✓ Actionable recommendations")
    print("  ✓ Risk scoring and categorization")


if __name__ == "__main__":
    main()
