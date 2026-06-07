#!/usr/bin/env python3
"""
Semi-automated curation workflow using PubMed API.

This script searches PubMed for enzyme-related papers about drugs
and extracts potential enzyme data for manual curation.
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api_clients import PubMedClient


class EnzymeDataExtractor:
    """Extract enzyme data from PubMed abstracts using pattern matching."""
    
    # Patterns for inhibition data
    INHIBITION_PATTERNS = [
        r"(?:inhibits?|inhibition of)\s+(\w+)\s+(?:with\s+)?(?:an?\s+)?(?:IC50|Ki)\s+of\s+([\d.]+)\s*(?:µM|uM|nM)",
        r"(\w+)\s+(?:was\s+)?(?:inhibited|inhibition)\s+(?:with\s+)?(?:IC50|Ki)\s+of\s+([\d.]+)\s*(?:µM|uM|nM)",
        r"(\w+)\s+(?:inhibitor|inhibition)\s+(?:IC50|Ki)\s*[:\s]*\s*([\d.]+)\s*(?:µM|uM|nM)",
    ]
    
    # Patterns for fm data
    FM_PATTERNS = [
        r"(\w+)\s+(?:metabolizes?|accounts?\s+for)\s+([\d.]+)\s*%\s+of",
        r"([\d.]+)\s*%\s+of\s+(?:the\s+)?(?:dose|drug)\s+(?:was\s+)?(?:metabolized\s+by\s+)?(\w+)",
    ]
    
    # Patterns for substrate mentions
    SUBSTRATE_PATTERNS = [
        r"(\w+)\s+(?:substrate|metabolized\s+by)",
        r"(?:substrate\s+of|metabolized\s+by)\s+(\w+)",
    ]
    
    def extract_from_abstract(self, abstract: str) -> Dict:
        """
        Extract enzyme data from abstract text.
        
        Args:
            abstract: Abstract text
        
        Returns:
            Dictionary with extracted enzyme data
        """
        extracted_data = {
            "inhibition": {},
            "fm": {},
            "substrate_mentions": set()
        }
        
        # Extract inhibition data
        for pattern in self.INHIBITION_PATTERNS:
            matches = re.finditer(pattern, abstract, re.IGNORECASE)
            for match in matches:
                enzyme = match.group(1)
                value = match.group(2)
                
                # Normalize enzyme name
                enzyme = self._normalize_enzyme_name(enzyme)
                if enzyme:
                    try:
                        ic50_value = float(value)
                        if enzyme not in extracted_data["inhibition"]:
                            extracted_data["inhibition"][enzyme] = []
                        extracted_data["inhibition"][enzyme].append({
                            "ic50_um": ic50_value,
                            "source": "PubMed abstract"
                        })
                    except:
                        pass
        
        # Extract fm data
        for pattern in self.FM_PATTERNS:
            matches = re.finditer(pattern, abstract, re.IGNORECASE)
            for match in matches:
                enzyme = match.group(1) if match.lastindex == 1 else match.group(2)
                value = match.group(2) if match.lastindex == 1 else match.group(1)
                
                # Normalize enzyme name
                enzyme = self._normalize_enzyme_name(enzyme)
                if enzyme:
                    try:
                        fm_value = float(value) / 100 if float(value) > 1 else float(value)
                        extracted_data["fm"][enzyme] = fm_value
                    except:
                        pass
        
        # Extract substrate mentions
        for pattern in self.SUBSTRATE_PATTERNS:
            matches = re.finditer(pattern, abstract, re.IGNORECASE)
            for match in matches:
                enzyme = match.group(1)
                enzyme = self._normalize_enzyme_name(enzyme)
                if enzyme:
                    extracted_data["substrate_mentions"].add(enzyme)
        
        # Convert set to list for JSON serialization
        extracted_data["substrate_mentions"] = list(extracted_data["substrate_mentions"])
        
        return extracted_data
    
    def _normalize_enzyme_name(self, name: str) -> Optional[str]:
        """Normalize enzyme name to standard format."""
        if not name:
            return None
        
        name_upper = name.upper()
        
        # Pattern matching for CYP enzymes
        cyp_patterns = [
            r"CYP\s*(\d+[A-Z]+\d*)",
            r"CYTOCHROME\s*P450\s*(\d+[A-Z]+\d*)",
            r"CYP-(\d+[A-Z]+\d*)"
        ]
        
        for pattern in cyp_patterns:
            match = re.search(pattern, name_upper)
            if match:
                return "CYP" + match.group(1)
        
        return None


def curate_drug_from_pubmed(drug_name: str, enzyme: str = None):
    """
    Curate enzyme data for a drug using PubMed.
    
    Args:
        drug_name: Name of the drug
        enzyme: Specific enzyme to search for (optional)
    """
    print(f"\n{'='*60}")
    print(f"Curating {drug_name} from PubMed")
    print(f"{'='*60}")
    
    pubmed = PubMedClient()
    extractor = EnzymeDataExtractor()
    
    # Search for papers
    print(f"\nSearching PubMed for {drug_name}...")
    if enzyme:
        print(f"  Enzyme: {enzyme}")
    papers = pubmed.search_enzyme_data(drug_name, enzyme)
    
    print(f"  Found {len(papers)} papers")
    
    if not papers:
        print("  No papers found")
        return
    
    # Extract data from papers
    all_extracted_data = {
        "inhibition": {},
        "fm": {},
        "substrate_mentions": [],
        "papers": []
    }
    
    for i, paper in enumerate(papers, 1):
        print(f"\n  Paper {i}:")
        print(f"    PMID: {paper['pmid']}")
        print(f"    Title: {paper['title'][:80]}...")
        print(f"    Journal: {paper['journal']}")
        print(f"    Year: {paper['year']}")
        
        # Extract enzyme data from abstract
        if paper['abstract']:
            extracted = extractor.extract_from_abstract(paper['abstract'])
            
            # Merge inhibition data
            for enzyme, data in extracted["inhibition"].items():
                if enzyme not in all_extracted_data["inhibition"]:
                    all_extracted_data["inhibition"][enzyme] = []
                all_extracted_data["inhibition"][enzyme].extend(data)
            
            # Merge fm data (keep first found)
            for enzyme, value in extracted["fm"].items():
                if enzyme not in all_extracted_data["fm"]:
                    all_extracted_data["fm"][enzyme] = value
            
            # Merge substrate mentions
            all_extracted_data["substrate_mentions"].extend(extracted["substrate_mentions"])
            
            # Store paper info
            all_extracted_data["papers"].append({
                "pmid": paper["pmid"],
                "title": paper["title"],
                "authors": paper["authors"],
                "journal": paper["journal"],
                "year": paper["year"],
                "abstract": paper["abstract"]
            })
            
            # Print extracted data
            if extracted["inhibition"]:
                print(f"    Inhibition data found: {list(extracted['inhibition'].keys())}")
            if extracted["fm"]:
                print(f"    FM data found: {extracted['fm']}")
            if extracted["substrate_mentions"]:
                print(f"    Substrate mentions: {extracted['substrate_mentions']}")
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"Inhibition data: {list(all_extracted_data['inhibition'].keys())}")
    print(f"FM data: {all_extracted_data['fm']}")
    print(f"Substrate mentions: {all_extracted_data['substrate_mentions']}")
    
    # Save results
    output_file = project_root / "data" / "pubmed_curation" / f"{drug_name.lower()}_pubmed_results.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(all_extracted_data, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print("\nNote: These results require manual validation before adding to curated data.")


def main():
    """Main function to run PubMed curation."""
    print("="*60)
    print("PubMed Curation Workflow")
    print("="*60)
    
    # Example: Curate midazolam
    drug_name = "midazolam"
    curate_drug_from_pubmed(drug_name)
    
    # Example: Curate ketoconazole with specific enzyme
    # drug_name = "ketoconazole"
    # curate_drug_from_pubmed(drug_name, enzyme="CYP3A4")


if __name__ == "__main__":
    main()
