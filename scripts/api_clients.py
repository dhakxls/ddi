#!/usr/bin/env python3
"""
API Clients for Drug Database Integration

Consolidated API clients for OpenFDA, PubChem, ChEMBL, and MyChem.info
"""

import requests
import json
import re
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time


@dataclass
class DrugData:
    """Consolidated drug data from multiple sources."""
    compound_name: str
    smiles: Optional[str] = None
    molecular_weight: Optional[float] = None
    logp: Optional[float] = None
    pka: Optional[float] = None
    polar_surface_area: Optional[float] = None
    enzyme_data: Optional[Dict] = None
    fm_data: Optional[Dict] = None
    sources: List[str] = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.enzyme_data is None:
            self.enzyme_data = {}
        if self.fm_data is None:
            self.fm_data = {}


class OpenFDAClient:
    """Client for OpenFDA API - FDA label data."""
    
    BASE_URL = "https://api.fda.gov/drug/label.json"
    RATE_LIMIT_DELAY = 0.25  # 240 requests/minute = ~0.25s between requests
    
    def __init__(self):
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Respect rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def get_drug_label(self, drug_name: str) -> Optional[Dict]:
        """
        Get FDA label data for a drug.
        
        Args:
            drug_name: Name of the drug
        
        Returns:
            Dictionary with label data or None if not found
        """
        self._rate_limit()
        
        params = {
            "search": f'openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}"',
            "limit": 1
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                return data["results"][0]
            return None
        except Exception as e:
            print(f"OpenFDA API error for {drug_name}: {e}")
            return None
    
    def extract_metabolism_data(self, label_data: Dict) -> Dict:
        """
        Extract metabolism data from FDA label.
        
        Args:
            label_data: FDA label data
        
        Returns:
            Dictionary with metabolism information
        """
        metabolism_info = {
            "enzymes": {},
            "fm_data": {},
            "clinical_pharmacology": ""
        }
        
        # Try to get Clinical Pharmacology section
        sections = label_data.get("clinical_pharmacology", [])
        if not sections:
            sections = label_data.get("pharmacokinetics", [])
        
        if sections:
            # Combine all sections (handle both strings and dicts)
            text_parts = []
            for s in sections:
                if isinstance(s, str):
                    text_parts.append(s)
                elif isinstance(s, dict):
                    # Extract text from dict
                    for key, value in s.items():
                        if isinstance(value, str):
                            text_parts.append(value)
            
            all_text = " ".join(text_parts)
            metabolism_info["clinical_pharmacology"] = all_text
            
            # Extract enzyme information using regex patterns
            enzyme_patterns = {
                "CYP3A4": r"CYP\s*3A4|CYP-3A4|cytochrome\s*P450\s*3A4",
                "CYP2D6": r"CYP\s*2D6|CYP-2D6|cytochrome\s*P450\s*2D6",
                "CYP2C9": r"CYP\s*2C9|CYP-2C9|cytochrome\s*P450\s*2C9",
                "CYP2C19": r"CYP\s*2C19|CYP-2C19|cytochrome\s*P450\s*2C19",
                "CYP1A2": r"CYP\s*1A2|CYP-1A2|cytochrome\s*P450\s*1A2",
                "CYP2B6": r"CYP\s*2B6|CYP-2B6|cytochrome\s*P450\s*2B6",
                "CYP2C8": r"CYP\s*2C8|CYP-2C8|cytochrome\s*P450\s*2C8",
                "CYP2E1": r"CYP\s*2E1|CYP-2E1|cytochrome\s*P450\s*2E1",
            }
            
            for enzyme, pattern in enzyme_patterns.items():
                if re.search(pattern, all_text, re.IGNORECASE):
                    metabolism_info["enzymes"][enzyme] = {
                        "mentioned": True,
                        "context": self._extract_context(all_text, enzyme)
                    }
            
            # Try to extract fraction metabolized (fm) data
            fm_patterns = [
                r"fraction\s*metabolized\s*by\s*CYP(\d+[A-Z]+\d*)\s*[:\s]*(\d+\.?\d*)",
                r"fm\s*[:\s]*(\d+\.?\d*)\s*%?\s*by\s*CYP(\d+[A-Z]+\d*)",
                r"(\d+\.?\d*)\s*%\s*of\s*the\s*dose\s*is\s*metabolized\s*by\s*CYP(\d+[A-Z]+\d*)",
                r"metabolized\s*primarily\s*by\s*CYP(\d+[A-Z]+\d*)",
                r"major\s*metabolic\s*pathway\s*is\s*CYP(\d+[A-Z]+\d*)",
            ]
            
            for pattern in fm_patterns:
                matches = re.finditer(pattern, all_text, re.IGNORECASE)
                for match in matches:
                    if pattern == fm_patterns[0]:  # fraction metabolized by CYP
                        enzyme = "CYP" + match.group(1)
                        fm_value = float(match.group(2))
                    elif pattern == fm_patterns[1]:  # fm by CYP
                        fm_value = float(match.group(1))
                        enzyme = "CYP" + match.group(2)
                    elif pattern == fm_patterns[2]:  # % of dose metabolized by CYP
                        fm_value = float(match.group(1)) / 100
                        enzyme = "CYP" + match.group(2)
                    elif pattern in [fm_patterns[3], fm_patterns[4]]:  # primarily/major pathway
                        enzyme = "CYP" + match.group(1)
                        fm_value = None  # Don't assume value - require explicit data
                    
                    # Normalize to 0-1 scale if > 1
                    if fm_value > 1:
                        fm_value = fm_value / 100
                    
                    metabolism_info["fm_data"][enzyme] = fm_value
        
        return metabolism_info
    
    def _extract_context(self, text: str, enzyme: str) -> str:
        """Extract context around enzyme mention."""
        pattern = rf".{{0,100}}{re.escape(enzyme)}.{{0,100}}"
        matches = re.finditer(pattern, text, re.IGNORECASE)
        contexts = [match.group() for match in matches]
        return " | ".join(contexts[:3])  # Return up to 3 contexts


class PubChemClient:
    """Client for PubChem API - chemical properties."""
    
    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    RATE_LIMIT_DELAY = 0.2  # 5 requests/second = 0.2s between requests
    
    def __init__(self):
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Respect rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def get_compound_info(self, drug_name: str) -> Optional[Dict]:
        """
        Get compound information from PubChem.
        
        Args:
            drug_name: Name of the drug
        
        Returns:
            Dictionary with compound data or None if not found
        """
        self._rate_limit()
        
        try:
            # Try getting CID first
            cid_response = requests.get(
                f"{self.BASE_URL}/compound/name/{drug_name}/cids/TXT",
                timeout=10
            )
            
            if cid_response.status_code != 200 or "Not Found" in cid_response.text:
                print(f"    CID not found for {drug_name}")
                return None
            
            cid = cid_response.text.strip()
            print(f"    Found CID: {cid}")
            
            # Get SMILES using CID
            self._rate_limit()
            smiles_response = requests.get(
                f"{self.BASE_URL}/compound/cid/{cid}/property/IsomericSMILES/TXT",
                timeout=10
            )
            
            smiles = None
            if smiles_response.status_code == 200 and "Not Found" not in smiles_response.text:
                smiles = smiles_response.text.strip()
            
            # Get Molecular Weight using CID
            self._rate_limit()
            mw_response = requests.get(
                f"{self.BASE_URL}/compound/cid/{cid}/property/MolecularWeight/TXT",
                timeout=10
            )
            
            mw = None
            if mw_response.status_code == 200 and "Not Found" not in mw_response.text:
                try:
                    mw = float(mw_response.text.strip())
                except:
                    mw = None
            
            if smiles or mw:
                return {
                    "cid": cid,
                    "properties": {
                        "IsomericSMILES": smiles,
                        "MolecularWeight": mw
                    }
                }
            
            return None
        except Exception as e:
            print(f"PubChem API error for {drug_name}: {e}")
            return None
    
    def extract_molecular_properties(self, compound_info: Dict) -> Dict:
        """
        Extract molecular properties from PubChem data.
        
        Args:
            compound_info: PubChem compound information
        
        Returns:
            Dictionary with molecular properties
        """
        props = compound_info.get("properties", {})
        
        return {
            "smiles": props.get("IsomericSMILES"),
            "molecular_weight": self._parse_float(props.get("MolecularWeight")),
            "logp": self._parse_float(props.get("XLogP3")),
            "exact_mass": self._parse_float(props.get("ExactMass")),
            "polar_surface_area": self._parse_float(props.get("TPSA"))
        }
    
    def _parse_float(self, value: Any) -> Optional[float]:
        """Parse float value from various formats."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


class ChEMBLClient:
    """Client for ChEMBL API - enzyme targets and bioactivity."""
    
    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
    RATE_LIMIT_DELAY = 0.2  # 5 requests/second
    
    def __init__(self):
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Respect rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def get_compound_targets(self, drug_name: str) -> Optional[Dict]:
        """
        Get compound targets from ChEMBL.
        
        Args:
            drug_name: Name of the drug
        
        Returns:
            Dictionary with target information or None if not found
        """
        self._rate_limit()
        
        try:
            # Search for molecule by name
            search_response = requests.get(
                f"{self.BASE_URL}/molecule/search.json?q={drug_name}",
                timeout=10
            )
            search_response.raise_for_status()
            
            search_data = search_response.json()
            if not search_data.get("molecules"):
                return None
            
            # Get first match
            molecule = search_data["molecules"][0]
            chembl_id = molecule.get("molecule_chembl_id")
            
            if not chembl_id:
                return None
            
            # Get activities/targets for this molecule
            self._rate_limit()
            activity_response = requests.get(
                f"{self.BASE_URL}/activity.json?molecule_chembl_id={chembl_id}&target_type=single+protein",
                timeout=10
            )
            activity_response.raise_for_status()
            
            activity_data = activity_response.json()
            activities = activity_data.get("activities", [])
            
            # Extract enzyme targets
            enzyme_targets = {}
            for activity in activities:
                target = activity.get("target_chembl_id")
                target_name = activity.get("target_pref_name")
                organism = activity.get("target_organism")
                
                if organism == "Homo sapiens" and target_name:
                    # Check if it's a CYP enzyme
                    if "CYP" in target_name.upper():
                        enzyme_name = self._normalize_enzyme_name(target_name)
                        if enzyme_name:
                            if enzyme_name not in enzyme_targets:
                                enzyme_targets[enzyme_name] = {
                                    "target_chembl_id": target,
                                    "activities": []
                                }
                            enzyme_targets[enzyme_name]["activities"].append({
                                "type": activity.get("standard_type"),
                                "value": activity.get("standard_value"),
                                "units": activity.get("standard_units")
                            })
            
            return {
                "chembl_id": chembl_id,
                "enzyme_targets": enzyme_targets
            }
        except Exception as e:
            print(f"ChEMBL API error for {drug_name}: {e}")
            return None
    
    def _normalize_enzyme_name(self, name: str) -> Optional[str]:
        """Normalize enzyme name to standard format."""
        # Convert to uppercase and standard format
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


class MyChemClient:
    """Client for MyChem.info API - aggregated drug data."""
    
    BASE_URL = "https://mychem.info/v1"
    RATE_LIMIT_DELAY = 1.0  # 1000 requests/day = ~1 request per minute safe
    
    def __init__(self):
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Respect rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def get_drug_info(self, drug_name: str) -> Optional[Dict]:
        """
        Get aggregated drug information from MyChem.info.
        
        Args:
            drug_name: Name of the drug
        
        Returns:
            Dictionary with drug information or None if not found
        """
        self._rate_limit()
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/compound/{drug_name}",
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("data"):
                return data["data"]
            
            return None
        except Exception as e:
            print(f"MyChem.info API error for {drug_name}: {e}")
            return None
    
    def extract_metabolism_data(self, drug_info: Dict) -> Dict:
        """
        Extract metabolism data from MyChem.info response.
        
        Args:
            drug_info: MyChem.info drug information
        
        Returns:
            Dictionary with metabolism information
        """
        metabolism_info = {
            "enzymes": {},
            "fm_data": {},
            "sources": []
        }
        
        # Check DrugBank data (aggregated)
        if "drugbank" in drug_info:
            drugbank_data = drug_info["drugbank"]
            metabolism_info["sources"].append("DrugBank")
            
            # Extract metabolism information
            if "metabolism" in drugbank_data:
                metabolism = drugbank_data["metabolism"]
                
                # Look for enzyme information
                if isinstance(metabolism, list):
                    for item in metabolism:
                        if isinstance(item, dict):
                            enzyme = item.get("enzyme")
                            if enzyme:
                                enzyme_name = self._normalize_enzyme_name(enzyme)
                                if enzyme_name:
                                    metabolism_info["enzymes"][enzyme_name] = {
                                        "mentioned": True,
                                        "source": "DrugBank"
                                    }
                            
                            # Look for fm data
                            fm = item.get("fraction")
                            if fm and enzyme_name:
                                try:
                                    fm_value = float(fm)
                                    if fm_value > 1:
                                        fm_value = fm_value / 100
                                    metabolism_info["fm_data"][enzyme_name] = fm_value
                                except:
                                    pass
        
        # Check other sources
        if "chembl" in drug_info:
            metabolism_info["sources"].append("ChEMBL")
        
        if "wikidata" in drug_info:
            metabolism_info["sources"].append("Wikidata")
        
        return metabolism_info
    
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


class PubMedClient:
    """Client for PubMed API to search literature for enzyme data."""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    RATE_LIMIT_DELAY = 1.0  # Increased to avoid rate limit errors
    
    def __init__(self):
        self.last_request_time = 0
        self.cache_dir = Path(__file__).parent.parent / "data" / "cache" / "pubmed"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _rate_limit(self):
        """Respect rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def search_papers(self, query: str, max_results: int = 20) -> List[Dict]:
        """
        Search PubMed for papers matching a query.
        
        Args:
            query: Search query (e.g., "midazolam CYP3A4 metabolism")
            max_results: Maximum number of results to return
        
        Returns:
            List of paper dictionaries with PMIDs
        """
        cache_path = self._search_cache_path(query, max_results)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    cached_pmids = json.load(f)
                return [{"pmid": pmid} for pmid in cached_pmids]
            except Exception:
                pass

        self._rate_limit()
        
        try:
            # Search for papers
            search_response = requests.get(
                f"{self.BASE_URL}/esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": query,
                    "retmode": "json",
                    "retmax": max_results
                },
                timeout=10
            )
            search_response.raise_for_status()
            
            search_data = search_response.json()
            pmids = search_data.get("esearchresult", {}).get("idlist", [])
            
            try:
                with open(cache_path, 'w') as f:
                    json.dump(pmids, f)
            except Exception:
                pass
            
            return [{"pmid": pmid} for pmid in pmids]
        except Exception as e:
            print(f"PubMed search error: {e}")
            return []
    
    def get_abstract(self, pmid: str) -> Optional[Dict]:
        """
        Get abstract for a paper by PMID.
        
        Args:
            pmid: PubMed ID
        
        Returns:
            Dictionary with paper metadata and abstract
        """
        cache_path = self._abstract_cache_path(pmid)
        if cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass

        self._rate_limit()
        
        try:
            # Fetch abstract
            fetch_response = requests.get(
                f"{self.BASE_URL}/efetch.fcgi",
                params={
                    "db": "pubmed",
                    "id": pmid,
                    "retmode": "xml"
                },
                timeout=10
            )
            fetch_response.raise_for_status()
            
            # Parse XML response
            import xml.etree.ElementTree as ET
            root = ET.fromstring(fetch_response.text)
            
            # Extract paper data
            paper_data = {
                "pmid": pmid,
                "title": "",
                "abstract": "",
                "authors": [],
                "journal": "",
                "year": ""
            }
            
            # Extract title
            title_elem = root.find(".//ArticleTitle")
            if title_elem is not None and title_elem.text:
                paper_data["title"] = title_elem.text
            
            # Extract abstract
            abstract_elem = root.find(".//AbstractText")
            if abstract_elem is not None and abstract_elem.text:
                paper_data["abstract"] = abstract_elem.text
            
            # Extract authors
            author_list = root.find(".//AuthorList")
            if author_list is not None:
                for author in author_list.findall(".//Author"):
                    last_name = author.find(".//LastName")
                    initials = author.find(".//Initials")
                    if last_name is not None and initials is not None:
                        paper_data["authors"].append(f"{last_name.text} {initials.text}")
            
            # Extract journal
            journal_elem = root.find(".//Journal/Title")
            if journal_elem is not None and journal_elem.text:
                paper_data["journal"] = journal_elem.text
            
            # Extract year
            year_elem = root.find(".//PubDate/Year")
            if year_elem is not None and year_elem.text:
                paper_data["year"] = year_elem.text
            
            try:
                with open(cache_path, 'w') as f:
                    json.dump(paper_data, f)
            except Exception:
                pass
            
            return paper_data
        except Exception as e:
            print(f"PubMed abstract fetch error for PMID {pmid}: {e}")
            return None

    def _search_cache_path(self, query: str, max_results: int) -> Path:
        key = hashlib.sha1(f"{query}|{max_results}".encode("utf-8")).hexdigest()
        return self.cache_dir / f"search_{key}.json"

    def _abstract_cache_path(self, pmid: str) -> Path:
        return self.cache_dir / f"abstract_{pmid}.json"
    
    def search_enzyme_data(self, drug_name: str, enzyme: str = None) -> List[Dict]:
        """
        Search PubMed for enzyme-related papers about a drug.
        
        Args:
            drug_name: Name of the drug
            enzyme: Specific enzyme to search for (optional)
        
        Returns:
            List of papers with abstracts
        """
        # Build search query
        if enzyme:
            query = f'"{drug_name}" AND "{enzyme}" AND (metabolism OR inhibition OR induction OR substrate)'
        else:
            query = f'"{drug_name}" AND (CYP OR metabolism OR pharmacokinetics)'
        
        # Search for papers
        papers = self.search_papers(query, max_results=10)
        
        # Fetch abstracts
        results = []
        for paper in papers:
            abstract_data = self.get_abstract(paper["pmid"])
            if abstract_data:
                results.append(abstract_data)
        
        return results


class DrugBankClient:
    """Client for DrugBank API - comprehensive drug data including enzyme data."""
    
    BASE_URL = "https://go.drugbank.com/api/v1"
    RATE_LIMIT_DELAY = 0.34  # ~3000 requests/month = ~1 request per minute safe
    
    def __init__(self, api_key: str = None):
        """
        Initialize DrugBank client.
        
        Args:
            api_key: DrugBank API key (development key is free with 3000 requests/month)
                    Get from: https://dev.drugbank.com/guides/api
        """
        self.api_key = api_key or os.environ.get("DRUGBANK_API_KEY")
        self.last_request_time = 0
        
        if not self.api_key:
            print("WARNING: No DrugBank API key provided")
            print("Get a free development key from: https://dev.drugbank.com/guides/api")
            print("Set DRUGBANK_API_KEY environment variable or pass api_key parameter")
    
    def _rate_limit(self):
        """Respect rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()
    
    def _get_headers(self):
        """Get request headers with API key."""
        if not self.api_key:
            raise ValueError("DrugBank API key required")
        return {"Authorization": f"Bearer {self.api_key}"}
    
    def get_drug_by_name(self, drug_name: str) -> Optional[Dict]:
        """
        Get drug data by name from DrugBank.
        
        Args:
            drug_name: Name of the drug
        
        Returns:
            Dictionary with drug data or None if not found
        """
        if not self.api_key:
            print("    Skipping DrugBank: No API key")
            return None
        
        self._rate_limit()
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/drugs/search",
                params={"query": drug_name, "limit": 1},
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 401:
                print("    DrugBank API: Invalid API key")
                return None
            elif response.status_code == 403:
                print("    DrugBank API: Forbidden (check API key permissions)")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                drug_id = data[0].get("drugbank_id")
                if drug_id:
                    # Get full drug details
                    return self.get_drug_by_id(drug_id)
            
            return None
        except Exception as e:
            print(f"    DrugBank API error for {drug_name}: {e}")
            return None
    
    def get_drug_by_id(self, drugbank_id: str) -> Optional[Dict]:
        """
        Get drug data by DrugBank ID.
        
        Args:
            drugbank_id: DrugBank ID (e.g., DB00641)
        
        Returns:
            Dictionary with drug data or None if not found
        """
        if not self.api_key:
            return None
        
        self._rate_limit()
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/drugs/{drugbank_id}",
                headers=self._get_headers(),
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"    DrugBank API error for {drugbank_id}: {e}")
            return None
    
    def extract_enzyme_data(self, drug_data: Dict) -> Dict:
        """
        Extract enzyme data from DrugBank response.
        
        Args:
            drug_data: DrugBank drug data
        
        Returns:
            Dictionary with enzyme information
        """
        enzyme_info = {
            "substrate": {},
            "inhibition": {},
            "induction": {},
            "fm_data": {}
        }
        
        if not drug_data:
            return enzyme_info
        
        # Extract metabolism data
        metabolism = drug_data.get("metabolism", {})
        
        # Get enzymes that metabolize this drug (substrates)
        pathways = metabolism.get("pathways", [])
        for pathway in pathways:
            enzymes = pathway.get("enzymes", [])
            for enzyme in enzymes:
                enzyme_name = self._normalize_enzyme_name(enzyme.get("name", ""))
                if enzyme_name:
                    if enzyme_name not in enzyme_info["substrate"]:
                        enzyme_info["substrate"][enzyme_name] = {
                            "is_substrate": True,
                            "source": "DrugBank"
                        }
        
        # Get drug as inhibitor/inducer from drug interactions
        drug_interactions = drug_data.get("drug_interactions", [])
        for interaction in drug_interactions:
            interaction_type = interaction.get("kind", "")
            if interaction_type in ["inhibitor", "inducer"]:
                # This drug is an inhibitor/inducer of the other drug
                # Need to look at the other drug's metabolism to find the enzyme
                other_drug_id = interaction.get("drugbank_id")
                if other_drug_id:
                    # Could recursively fetch other drug's metabolism
                    # For now, just note the interaction type
                    pass
        
        # Check if DrugBank has explicit enzyme data
        # Some DrugBank entries have direct enzyme annotations
        if "enzymes" in drug_data:
            for enzyme_data in drug_data["enzymes"]:
                enzyme_name = self._normalize_enzyme_name(enzyme_data.get("name", ""))
                if enzyme_name:
                    # Check relationship type
                    if enzyme_data.get("is_substrate"):
                        enzyme_info["substrate"][enzyme_name] = {
                            "is_substrate": True,
                            "source": "DrugBank"
                        }
                    if enzyme_data.get("is_inhibitor"):
                        enzyme_info["inhibition"][enzyme_name] = {
                            "is_inhibitor": True,
                            "source": "DrugBank"
                        }
                    if enzyme_data.get("is_inducer"):
                        enzyme_info["induction"][enzyme_name] = {
                            "is_inducer": True,
                            "source": "DrugBank"
                        }
                    
                    # Check for fraction metabolized
                    fm = enzyme_data.get("fraction_metabolized")
                    if fm:
                        try:
                            fm_value = float(fm)
                            if fm_value > 1:
                                fm_value = fm_value / 100
                            enzyme_info["fm_data"][enzyme_name] = fm_value
                        except:
                            pass
        
        return enzyme_info
    
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


class DataMerger:
    """Merge data from multiple API sources."""
    
    def __init__(self):
        self.openfda = OpenFDAClient()
        self.pubchem = PubChemClient()
        self.chembl = ChEMBLClient()
        self.mychem = MyChemClient()
        self.pubmed = PubMedClient()
        self.drugbank = DrugBankClient()
    
    def get_consolidated_drug_data(self, drug_name: str) -> DrugData:
        """
        Get consolidated drug data from all available sources.
        
        Args:
            drug_name: Name of the drug
        
        Returns:
            DrugData object with consolidated information
        """
        drug_data = DrugData(compound_name=drug_name)
        
        # Query OpenFDA
        print(f"  Querying OpenFDA for {drug_name}...")
        openfda_data = self.openfda.get_drug_label(drug_name)
        if openfda_data:
            drug_data.sources.append("OpenFDA")
            metabolism = self.openfda.extract_metabolism_data(openfda_data)
            if metabolism.get("fm_data"):
                drug_data.fm_data = metabolism["fm_data"]
                print(f"    ✓ Found fm data: {drug_data.fm_data}")
            else:
                print(f"    ℹ No fm data found in OpenFDA")
                # Debug: show what we got
                if metabolism.get("enzymes"):
                    print(f"    ℹ Enzymes mentioned: {list(metabolism['enzymes'].keys())}")
                # Debug: show sample of clinical pharmacology text
                if metabolism.get("clinical_pharmacology"):
                    sample = metabolism["clinical_pharmacology"][:200]
                    print(f"    ℹ Sample text: {sample}...")
        
        # Query PubChem
        print(f"  Querying PubChem for {drug_name}...")
        pubchem_data = self.pubchem.get_compound_info(drug_name)
        if pubchem_data:
            drug_data.sources.append("PubChem")
            props = self.pubchem.extract_molecular_properties(pubchem_data)
            drug_data.smiles = props.get("smiles")
            drug_data.molecular_weight = props.get("molecular_weight")
            drug_data.logp = props.get("logp")
            drug_data.polar_surface_area = props.get("polar_surface_area")
            print(f"    ✓ Found SMILES: {drug_data.smiles}")
            print(f"    ✓ Found MW: {drug_data.molecular_weight}")
        else:
            print(f"    ✗ PubChem data not found")
        
        # Query ChEMBL
        print(f"  Querying ChEMBL for {drug_name}...")
        chembl_data = self.chembl.get_compound_targets(drug_name)
        if chembl_data and chembl_data.get("enzyme_targets"):
            drug_data.sources.append("ChEMBL")
            # Merge enzyme targets
            for enzyme, target_info in chembl_data["enzyme_targets"].items():
                if enzyme not in drug_data.enzyme_data:
                    drug_data.enzyme_data[enzyme] = {
                        "mentioned": True,
                        "source": "ChEMBL",
                        "activities": target_info.get("activities", [])
                    }
            print(f"    ✓ Found enzyme targets: {list(chembl_data['enzyme_targets'].keys())}")
        else:
            print(f"    ℹ ChEMBL no enzyme targets found")
        
        # Query MyChem.info
        print(f"  Querying MyChem.info for {drug_name}...")
        mychem_data = self.mychem.get_drug_info(drug_name)
        if mychem_data:
            drug_data.sources.append("MyChem.info")
            metabolism = self.mychem.extract_metabolism_data(mychem_data)
            
            # Merge fm data
            if metabolism.get("fm_data"):
                for enzyme, fm_value in metabolism["fm_data"].items():
                    if enzyme not in drug_data.fm_data:
                        drug_data.fm_data[enzyme] = fm_value
                print(f"    ✓ Found fm data: {drug_data.fm_data}")
            
            # Merge enzyme data
            if metabolism.get("enzymes"):
                for enzyme, info in metabolism["enzymes"].items():
                    if enzyme not in drug_data.enzyme_data:
                        drug_data.enzyme_data[enzyme] = info
                print(f"    ✓ Found enzyme data: {list(metabolism['enzymes'].keys())}")
        else:
            print(f"    ✗ MyChem.info data not found")
        
        # Query DrugBank (if API key available)
        print(f"  Querying DrugBank for {drug_name}...")
        drugbank_data = self.drugbank.get_drug_by_name(drug_name)
        if drugbank_data:
            drug_data.sources.append("DrugBank")
            metabolism = self.drugbank.extract_enzyme_data(drugbank_data)
            
            # Merge enzyme data from DrugBank
            if metabolism.get("substrate"):
                for enzyme, info in metabolism["substrate"].items():
                    if enzyme not in drug_data.enzyme_data:
                        drug_data.enzyme_data[enzyme] = info
                print(f"    ✓ Found DrugBank substrate data: {list(metabolism['substrate'].keys())}")
            
            if metabolism.get("inhibition"):
                for enzyme, info in metabolism["inhibition"].items():
                    if enzyme not in drug_data.enzyme_data:
                        drug_data.enzyme_data[enzyme] = info
                print(f"    ✓ Found DrugBank inhibition data: {list(metabolism['inhibition'].keys())}")
            
            if metabolism.get("induction"):
                for enzyme, info in metabolism["induction"].items():
                    if enzyme not in drug_data.enzyme_data:
                        drug_data.enzyme_data[enzyme] = info
                print(f"    ✓ Found DrugBank induction data: {list(metabolism['induction'].keys())}")
            
            # Merge fm data from DrugBank
            if metabolism.get("fm_data"):
                for enzyme, fm_value in metabolism["fm_data"].items():
                    if enzyme not in drug_data.fm_data:
                        drug_data.fm_data[enzyme] = fm_value
                print(f"    ✓ Found DrugBank fm data: {drug_data.fm_data}")
        else:
            print(f"    ℹ DrugBank data not available (requires API key)")
        
        print(f"\n  Summary for {drug_name}:")
        print(f"    Sources: {drug_data.sources}")
        print(f"    SMILES: {drug_data.smiles}")
        print(f"    MW: {drug_data.molecular_weight}")
        print(f"    Enzyme Data: {list(drug_data.enzyme_data.keys()) if drug_data.enzyme_data else 'None'}")
        print(f"    fm Data: {drug_data.fm_data}")
        
        return drug_data


def test_api_clients():
    """Test API clients with Tier 1 compounds."""
    merger = DataMerger()
    
    # Test with 3 compounds first to see if new APIs help
    test_compounds = ["Midazolam", "Fluoxetine", "Warfarin"]
    
    print("="*60)
    print("Testing API Clients - Including ChEMBL and MyChem.info")
    print("="*60)
    
    results = {}
    for compound in test_compounds:
        print(f"\nTesting {compound}...")
        data = merger.get_consolidated_drug_data(compound)
        results[compound] = data
    
    print("\n" + "="*60)
    print("Test Complete - Summary")
    print("="*60)
    
    # Coverage summary
    smiles_count = sum(1 for d in results.values() if d.smiles)
    mw_count = sum(1 for d in results.values() if d.molecular_weight)
    fm_count = sum(1 for d in results.values() if d.fm_data)
    enzyme_count = sum(1 for d in results.values() if d.enzyme_data)
    
    print(f"\nCoverage ({len(test_compounds)} compounds):")
    print(f"  SMILES: {smiles_count}/{len(test_compounds)} ({smiles_count/len(test_compounds)*100:.0f}%)")
    print(f"  Molecular Weight: {mw_count}/{len(test_compounds)} ({mw_count/len(test_compounds)*100:.0f}%)")
    print(f"  Enzyme Data: {enzyme_count}/{len(test_compounds)} ({enzyme_count/len(test_compounds)*100:.0f}%)")
    print(f"  fm Data: {fm_count}/{len(test_compounds)} ({fm_count/len(test_compounds)*100:.0f}%)")
    
    # Compounds with fm data
    if fm_count > 0:
        print(f"\nCompounds with fm data:")
        for name, data in results.items():
            if data.fm_data:
                print(f"  {name}: {data.fm_data}")
    
    # Compounds with enzyme data
    if enzyme_count > 0:
        print(f"\nCompounds with enzyme data:")
        for name, data in results.items():
            if data.enzyme_data:
                print(f"  {name}: {list(data.enzyme_data.keys())}")
    
    return results


if __name__ == "__main__":
    test_api_clients()
