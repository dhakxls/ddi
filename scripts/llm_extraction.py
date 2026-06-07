#!/usr/bin/env python3
"""
LLM-based automated extraction of enzyme data from PubMed abstracts.

This script uses OpenAI API to extract structured enzyme data from
PubMed abstracts, reducing manual curation effort.
"""

import sys
import json
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api_clients import PubMedClient, DataMerger


class LLMEnzymeExtractor:
    """Extract enzyme data using local LLM (Ollama)."""
    
    def __init__(self, model: str = "llama3"):
        """
        Initialize LLM extractor.
        
        Args:
            model: Ollama model name (default: llama2)
        """
        self.model = model
        self.cache_dir = project_root / "data" / "cache" / "llm"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        try:
            import requests
            self.requests = requests
            # Check if Ollama is running
            response = self.requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code != 200:
                raise ConnectionError("Ollama not running. Start with: ollama serve")
        except Exception as e:
            raise ConnectionError(f"Ollama not available: {e}. Install Ollama and run 'ollama serve'")
    
    def extract_from_abstract(self, abstract: str, drug_name: str) -> Dict:
        """
        Extract enzyme data from abstract using LLM.
        
        Args:
            abstract: Abstract text
            drug_name: Name of the drug
        
        Returns:
            Dictionary with extracted enzyme data
        """
        json_format = '{"substrate": {"CYP3A4": {"is_substrate": true, "fm": 0.9}}}, "inhibition": {"CYP3A4": {"is_inhibitor": true, "inhibition_type": "strong", "ic50_um": 0.015}}}, "induction": {}, "confidence": "high"}'
        cache_key = hashlib.sha1(f"abstract::{self.model}::{drug_name}::{abstract}".encode("utf-8")).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        prompt = f"""You are a pharmacology expert extracting enzyme data from scientific literature.

Drug: {drug_name}

Extract the following information from the abstract below:
1. Enzyme substrate data: Which CYP enzymes metabolize this drug?
2. Enzyme inhibition data: Which CYP enzymes does this drug inhibit? What are the IC50/Ki values?
3. Enzyme induction data: Which CYP enzymes does this drug induce?
4. Fraction metabolized (fm): What fraction of the drug is metabolized by each enzyme?

CRITICAL RULES:
- ONLY extract data that is EXPLICITLY stated in the abstract
- Do NOT infer or assume enzyme relationships
- If the abstract does not mention a specific enzyme relationship, do NOT include it
- Be conservative - it's better to miss data than to hallucinate false information
- Only include enzymes that are specifically named in the context of metabolism/inhibition/induction
- Do NOT assume that because a drug is mentioned with an enzyme, it has a specific relationship

IMPORTANT: Return ONLY a valid JSON object. Do not include any text before or after the JSON.

Format:
{json_format}

Rules:
- Use only CYP enzymes (CYP1A2, CYP2B6, CYP2C8, CYP2C9, CYP2C19, CYP2D6, CYP2E1, CYP3A4, CYP3A5)
- Inhibition type: strong (IC50 < 1 µM), moderate (1-10 µM), weak (> 10 µM)
- fm values: decimal between 0 and 1
- If no data for a category, return empty object for that category
- Only extract data explicitly stated in abstract

Abstract:
{abstract}
"""
        try:
            response = self.requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for more conservative outputs
                        "top_p": 0.9
                    }
                },
                timeout=180
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Try to parse JSON from response
            response_text = result.get("response", "")
            
            # Try to find JSON in the response
            import re
            
            # First, try to find the first complete JSON object
            # Look for a pattern that starts with { and ends with }
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                try:
                    json_str = json_match.group()
                    # Clean up any trailing text/punctuation
                    json_str = json_str.strip()
                    # Remove any trailing non-JSON characters
                    while json_str and json_str[-1] not in '}':
                        json_str = json_str[:-1]
                    
                    extracted_data = json.loads(json_str)
                    # Validate structure
                    if "substrate" in extracted_data or "inhibition" in extracted_data:
                        self._write_cache(cache_file, extracted_data)
                        return extracted_data
                except Exception as e:
                    # Try alternative approach: find JSON between first { and last }
                    try:
                        first_brace = response_text.find('{')
                        last_brace = response_text.rfind('}')
                        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                            json_str = response_text[first_brace:last_brace+1]
                            extracted_data = json.loads(json_str)
                            if "substrate" in extracted_data or "inhibition" in extracted_data:
                                self._write_cache(cache_file, extracted_data)
                                return extracted_data
                    except Exception as e2:
                        pass
            
            # If JSON extraction failed, return empty structure
            print(f"  Warning: Could not parse JSON from LLM response")
            return {
                "substrate": {},
                "inhibition": {},
                "induction": {},
                "confidence": "low"
            }
        except Exception as e:
            print(f"  Error in LLM extraction: {e}")
            return {
                "substrate": {},
                "inhibition": {},
                "induction": {},
                "confidence": "low"
            }

    def _write_cache(self, cache_file: Path, data: Dict) -> None:
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def extract_from_structured_data(self, drug_name: str) -> Dict:
        """
        Extract enzyme data from structured database APIs using LLM.
        
        This method queries structured databases (OpenFDA, ChEMBL, MyChem.info)
        and has the LLM parse the structured JSON data instead of unstructured abstracts.
        
        Args:
            drug_name: Name of the drug
        
        Returns:
            Dictionary with extracted enzyme data
        """
        print(f"  Querying structured databases for {drug_name}...")
        
        # Get structured data from APIs
        merger = DataMerger()
        drug_data = merger.get_consolidated_drug_data(drug_name)
        
        # Convert to JSON string for LLM
        structured_data = {
            "drug_name": drug_name,
            "sources": drug_data.sources,
            "enzyme_data": drug_data.enzyme_data,
            "fm_data": drug_data.fm_data,
            "molecular_properties": {
                "smiles": drug_data.smiles,
                "molecular_weight": drug_data.molecular_weight,
                "logp": drug_data.logp
            }
        }
        
        structured_json = json.dumps(structured_data, indent=2)
        
        json_format = '{"substrate": {"CYP3A4": {"is_substrate": true, "fm": 0.9}}}, "inhibition": {"CYP3A4": {"is_inhibitor": true, "inhibition_type": "strong", "ic50_um": 0.015}}}, "induction": {}, "confidence": "high"}'
        
        prompt = f"""You are a pharmacology expert extracting enzyme data from structured database records.

Drug: {drug_name}

I have queried multiple structured databases (OpenFDA, ChEMBL, MyChem.info) for this drug.
Below is the structured JSON data returned by these APIs.

Extract the following information from the structured data:
1. Enzyme substrate data: Which CYP enzymes metabolize this drug?
2. Enzyme inhibition data: Which CYP enzymes does this drug inhibit? What are the IC50/Ki values?
3. Enzyme induction data: Which CYP enzymes does this drug induce?
4. Fraction metabolized (fm): What fraction of the drug is metabolized by each enzyme?

CRITICAL RULES:
- ONLY extract data that is EXPLICITLY present in the structured data
- The data is already structured - do NOT infer or assume relationships
- If the structured data does not mention a specific enzyme relationship, do NOT include it
- Be conservative - it's better to miss data than to hallucinate false information
- Only include enzymes that are explicitly listed in the enzyme_data or fm_data fields
- Pay attention to activity types (IC50, Ki values) to determine inhibition strength

IMPORTANT: Return ONLY a valid JSON object. Do not include any text before or after the JSON.

Format:
{json_format}

Rules:
- Use only CYP enzymes (CYP1A2, CYP2B6, CYP2C8, CYP2C9, CYP2C19, CYP2D6, CYP2E1, CYP3A4, CYP3A5)
- Inhibition type: strong (IC50 < 1 µM), moderate (1-10 µM), weak (> 10 µM)
- fm values: decimal between 0 and 1
- If no data for a category, return empty object for that category
- Only extract data explicitly present in the structured JSON

Structured Data:
{structured_json}
"""
        try:
            response = self.requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                },
                timeout=180
            )
            response.raise_for_status()
            
            result = response.json()
            response_text = result.get("response", "")
            
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                try:
                    json_str = json_match.group()
                    json_str = json_str.strip()
                    while json_str and json_str[-1] not in '}':
                        json_str = json_str[:-1]
                    
                    extracted_data = json.loads(json_str)
                    if "substrate" in extracted_data or "inhibition" in extracted_data:
                        return extracted_data
                except Exception as e:
                    try:
                        first_brace = response_text.find('{')
                        last_brace = response_text.rfind('}')
                        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                            json_str = response_text[first_brace:last_brace+1]
                            extracted_data = json.loads(json_str)
                            if "substrate" in extracted_data or "inhibition" in extracted_data:
                                return extracted_data
                    except Exception as e2:
                        pass
            
            print(f"  Warning: Could not parse JSON from LLM response")
            return {
                "substrate": {},
                "inhibition": {},
                "induction": {},
                "confidence": "low"
            }
        except Exception as e:
            print(f"  Error in LLM extraction: {e}")
            return {
                "substrate": {},
                "inhibition": {},
                "induction": {},
                "confidence": "low"
            }


def curate_drug_with_llm(drug_name: str, max_papers: int = 10, model: str = "llama3"):
    """
    Curate enzyme data for a drug using LLM extraction from PubMed.
    
    Args:
        drug_name: Name of the drug
        max_papers: Maximum number of papers to process
        model: Ollama model name
    """
    print(f"\n{'='*60}")
    print(f"LLM-based Curation for {drug_name}")
    print(f"Using model: {model}")
    print(f"{'='*60}")
    
    # Initialize clients
    pubmed = PubMedClient()
    try:
        extractor = LLMEnzymeExtractor(model=model)
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nTo use this script:")
        print("1. Install Ollama: https://ollama.ai")
        print("2. Run Ollama: ollama serve")
        print("3. Pull a model: ollama pull llama2")
        print("4. Run script: python3 scripts/llm_extraction.py")
        return
    
    # Search for papers
    print(f"\nSearching PubMed for {drug_name}...")
    papers = pubmed.search_enzyme_data(drug_name)
    
    if not papers:
        print("  No papers found")
        return
    
    print(f"  Found {len(papers)} papers")
    print(f"  Processing with LLM (max {max_papers} papers)...")
    
    # Extract data from papers using LLM
    all_extracted_data = {
        "substrate": {},
        "inhibition": {},
        "induction": {},
        "papers": []
    }
    
    for i, paper in enumerate(papers[:max_papers], 1):
        print(f"\n  Paper {i}/{min(len(papers), max_papers)}: {paper['title'][:60]}...")
        
        if not paper['abstract']:
            print("    No abstract available")
            continue
        
        # Extract with LLM
        extracted = extractor.extract_from_abstract(paper['abstract'], drug_name)
        
        # Merge data
        for enzyme, data in extracted.get("substrate", {}).items():
            if enzyme not in all_extracted_data["substrate"]:
                all_extracted_data["substrate"][enzyme] = data
            else:
                # Keep the data with fm value if available
                if data.get("fm") and not all_extracted_data["substrate"][enzyme].get("fm"):
                    all_extracted_data["substrate"][enzyme] = data
        
        for enzyme, data in extracted.get("inhibition", {}).items():
            if enzyme not in all_extracted_data["inhibition"]:
                all_extracted_data["inhibition"][enzyme] = data
            else:
                # Keep the stronger inhibition
                current_type = all_extracted_data["inhibition"][enzyme].get("inhibition_type", "weak")
                new_type = data.get("inhibition_type", "weak")
                if new_type in ["strong", "moderate"] and current_type == "weak":
                    all_extracted_data["inhibition"][enzyme] = data
        
        for enzyme, data in extracted.get("induction", {}).items():
            if enzyme not in all_extracted_data["induction"]:
                all_extracted_data["induction"][enzyme] = data
        
        # Store paper info
        all_extracted_data["papers"].append({
            "pmid": paper["pmid"],
            "title": paper["title"],
            "journal": paper["journal"],
            "year": paper["year"],
            "extracted_data": extracted
        })
        
        confidence = extracted.get("confidence", "low")
        print(f"    Confidence: {confidence}")
        if extracted.get("substrate"):
            print(f"    Substrates: {list(extracted['substrate'].keys())}")
        if extracted.get("inhibition"):
            print(f"    Inhibitions: {list(extracted['inhibition'].keys())}")
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"Substrate enzymes: {list(all_extracted_data['substrate'].keys())}")
    print(f"Inhibition enzymes: {list(all_extracted_data['inhibition'].keys())}")
    print(f"Induction enzymes: {list(all_extracted_data['induction'].keys())}")
    
    # Save results
    output_file = project_root / "data" / "llm_curation" / f"{drug_name.lower()}_llm_results.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(all_extracted_data, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print("\nNote: Review extracted data before adding to curated files.")


def curate_drug_with_structured_llm(drug_name: str, model: str = "llama3"):
    """
    Curate enzyme data for a drug using LLM extraction from structured databases.
    
    This method uses structured database APIs (OpenFDA, ChEMBL, MyChem.info)
    instead of unstructured PubMed abstracts.
    
    Args:
        drug_name: Name of the drug
        model: Ollama model name
    """
    print(f"\n{'='*60}")
    print(f"LLM-based Curation (Structured Data) for {drug_name}")
    print(f"Using model: {model}")
    print(f"{'='*60}")
    
    try:
        extractor = LLMEnzymeExtractor(model=model)
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nTo use this script:")
        print("1. Install Ollama: https://ollama.ai")
        print("2. Run Ollama: ollama serve")
        print("3. Pull a model: ollama pull llama3")
        print("4. Run script: python3 scripts/llm_extraction.py")
        return
    
    # Extract with LLM from structured data
    print(f"\nExtracting enzyme data from structured databases...")
    extracted = extractor.extract_from_structured_data(drug_name)
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"Substrate enzymes: {list(extracted['substrate'].keys())}")
    print(f"Inhibition enzymes: {list(extracted['inhibition'].keys())}")
    print(f"Induction enzymes: {list(extracted['induction'].keys())}")
    
    # Save results
    output_file = project_root / "data" / "llm_curation" / f"{drug_name.lower()}_structured_llm_results.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(extracted, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    print("\nNote: Review extracted data before adding to curated files.")
    
    return extracted


def main():
    """Main function to run LLM-based curation."""
    print("="*60)
    print("LLM-based Enzyme Data Extraction")
    print("="*60)
    
    # Example: Curate midazolam
    drug_name = "midazolam"
    curate_drug_with_llm(drug_name, model="llama3")


if __name__ == "__main__":
    main()
