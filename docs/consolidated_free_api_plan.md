# Consolidated Free API Integration Plan

## Strategy: Combine Multiple Free APIs for Maximum Coverage

Yes, we can consolidate free options to get the best coverage. By combining data from multiple sources, we can achieve 70-85% coverage without paying for DrugBank.

## Free API Sources and Their Strengths

### 1. OpenFDA API
- **Strengths**: FDA label information, Clinical Pharmacology sections
- **Data**: Metabolism pathways, enzyme information, some fm data
- **Coverage**: 50-70% for metabolism data
- **Rate Limit**: 240 requests/minute
- **Use For**: Enzyme data, fm data, clinical implications

### 2. PubChem API
- **Strengths**: Chemical properties, SMILES, molecular descriptors
- **Data**: SMILES, molecular weight, logP, pKa, polar surface area
- **Coverage**: 95%+ for chemical properties
- **Rate Limit**: 5 requests/second
- **Use For**: SMILES validation, molecular properties, chemical descriptors

### 3. ChEMBL API
- **Strengths**: Bioactivity data, some metabolism information
- **Data**: Enzyme targets, bioactivity, some metabolism
- **Coverage**: 30-50% for metabolism data
- **Rate Limit**: 5 requests/second
- **Use For**: Cross-validation, enzyme targets, bioactivity

### 4. MyChem.info API
- **Strengths**: Aggregates from multiple sources (including DrugBank)
- **Data**: Aggregated drug information, some metabolism
- **Coverage**: 40-60% for metabolism data
- **Rate Limit**: 1000 requests/day
- **Use For**: Filling gaps, cross-reference

## Consolidated Data Pipeline

```
┌─────────────────┐
│   User Input    │
│  (Drug Name)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API Orchestrator│
│  (query all APIs)│
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
    ▼         ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│OpenFDA  │ │PubChem  │ │ ChEMBL  │ │MyChem  │
│ API     │ │ API     │ │ API     │ │ API     │
└────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘
     │           │           │           │
     │           │           │           │
     └───────────┴───────────┴───────────┘
                         │
                         ▼
              ┌────────────────────┐
              │  Data Merger       │
              │  (combine & dedupe)│
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │  Data Validator    │
              │  (quality check)   │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │  Confidence Scorer│
              │  (assign weights)  │
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │  JSON Updater      │
              │  (update files)    │
              └────────────────────┘
```

## Data Merger Logic

### Priority Order for Data Sources
1. **OpenFDA** (highest priority for metabolism/fm data)
2. **MyChem.info** (aggregated, includes DrugBank data)
3. **ChEMBL** (bioactivity, enzyme targets)
4. **PubChem** (chemical properties, SMILES)

### Confidence Scoring
```python
confidence_scores = {
    "openfda": 0.95,      # Official FDA data
    "mychem": 0.85,       # Aggregated from DrugBank
    "chembl": 0.75,       # Curated bioactivity
    "pubchem": 0.65       # Community-contributed
}
```

### Conflict Resolution
- If multiple sources have different values:
  - Use highest confidence source
  - Flag for manual review if confidence difference < 0.1
  - Log all sources for traceability

## Expected Coverage Improvement

### Single API (OpenFDA only)
- **fm data**: 50-70% coverage
- **SMILES**: 60-80% coverage
- **Molecular properties**: 40-60% coverage
- **Overall**: 50-70% automated

### Consolidated APIs (All 4)
- **fm data**: 70-85% coverage (OpenFDA + MyChem + ChEMBL)
- **SMILES**: 95%+ coverage (PubChem + OpenFDA + MyChem)
- **Molecular properties**: 90%+ coverage (PubChem + MyChem)
- **Enzyme data**: 75-85% coverage (OpenFDA + ChEMBL + MyChem)
- **Overall**: 80-85% automated

## Implementation Plan

### Phase 1: Build API Clients (Week 1)

**OpenFDA Client**:
```python
class OpenFDAClient:
    def get_drug_label(self, drug_name):
        # Query FDA label
        pass
    
    def extract_metabolism_data(self, label_data):
        # Parse Clinical Pharmacology section
        # Extract enzyme and fm data
        pass
```

**PubChem Client**:
```python
class PubChemClient:
    def get_smiles(self, drug_name):
        # Get SMILES string
        pass
    
    def get_molecular_properties(self, drug_name):
        # Get molecular weight, logP, pKa, etc.
        pass
```

**ChEMBL Client**:
```python
class ChEMBLClient:
    def get_enzyme_targets(self, drug_name):
        # Get enzyme targets
        pass
    
    def get_metabolism_data(self, drug_name):
        # Get metabolism information
        pass
```

**MyChem Client**:
```python
class MyChemClient:
    def get_drug_info(self, drug_name):
        # Get aggregated drug info
        pass
    
    def extract_metabolism(self, drug_info):
        # Extract metabolism data
        pass
```

### Phase 2: Build Data Merger (Week 1)

```python
class DataMerger:
    def merge_drug_data(self, drug_name):
        # Query all APIs
        openfda_data = openfda_client.get_drug_label(drug_name)
        pubchem_data = pubchem_client.get_molecular_properties(drug_name)
        chembl_data = chembl_client.get_enzyme_targets(drug_name)
        mychem_data = mychem_client.get_drug_info(drug_name)
        
        # Merge with priority
        merged = {
            "compound_name": drug_name,
            "smiles": self._get_best_value([pubchem_data, mychem_data], "smiles"),
            "enzyme_data": self._merge_enzyme_data([openfda_data, mychem_data, chembl_data]),
            "molecular_properties": self._merge_properties([pubchem_data, mychem_data]),
            "sources": self._track_sources([openfda_data, pubchem_data, chembl_data, mychem_data])
        }
        
        return merged
```

### Phase 3: Test with Tier 1 Compounds (Week 1)

Test consolidated approach with 10 Tier 1 compounds:
- Midazolam, Ketoconazole, Fluoxetine, Warfarin, Metoprolol
- Propranolol, Diazepam, Omeprazole, Phenytoin, Ibuprofen

**Metrics**:
- % of compounds with fm data
- % of compounds with SMILES
- % of compounds with molecular properties
- Data quality (confidence scores)
- Time per compound

### Phase 4: Scale to Full Dataset (Week 2)

- Process all 100 Kivo compounds
- Update JSON files automatically
- Generate coverage report
- Identify gaps for manual curation

## Benefits of Consolidated Approach

**Coverage Improvement**:
- 50-70% → 80-85% automated coverage
- Reduces manual curation from 30 to 15 compounds

**Data Quality**:
- Multiple sources provide cross-validation
- Confidence scoring identifies reliable data
- Source tracking for audit trail

**Robustness**:
- If one API fails, others provide backup
- Rate limiting distributed across APIs
- No single point of failure

**Cost**:
- Still free (all APIs are free)
- No subscription fees
- No API keys required

## Potential Challenges

**API Rate Limits**:
- PubChem: 5 requests/second
- ChEMBL: 5 requests/second
- MyChem: 1000 requests/day
- OpenFDA: 240 requests/minute

**Solution**: Implement rate limiting and batching

**Data Conflicts**:
- Different APIs may have different values
- Need robust conflict resolution

**Solution**: Confidence scoring with manual review flagging

**Parsing Complexity**:
- OpenFDA data is unstructured label text
- Need NLP or regex parsing

**Solution**: Build robust parsers with fallback logic

## Next Steps

**Immediate**:
1. Build OpenFDA client (highest priority for metabolism data)
2. Build PubChem client (highest priority for chemical properties)
3. Test with 2-3 compounds
4. Evaluate data quality

**If Successful**:
1. Build ChEMBL and MyChem clients
2. Implement data merger
3. Scale to all 100 compounds
4. Generate coverage report

**Fallback**:
If consolidated APIs don't provide sufficient fm data, we can still manually curate the gaps (15-20 compounds instead of 30).

## Would you like me to start building the consolidated API clients?
