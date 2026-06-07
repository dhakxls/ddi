# Drug Database API Integration Plan

## Available Drug Database APIs

### 1. DrugBank API (Paid)
- **URL**: https://go.drugbank.com/releases/latest
- **Cost**: Paid subscription (academic pricing available)
- **Data Quality**: Excellent - comprehensive metabolism data
- **fm Data**: Yes, includes fraction metabolized
- **Rate Limits**: Depends on subscription tier
- **Pros**: Most comprehensive, high-quality data
- **Cons**: Cost barrier, requires API key

### 2. PubChem API (Free)
- **URL**: https://pubchem.ncbi.nlm.nih.gov/rest/
- **Cost**: Free
- **Data Quality**: Good for chemical properties, limited metabolism data
- **fm Data**: Limited - may have some but not comprehensive
- **Rate Limits**: 5 requests per second
- **Pros**: Free, no API key needed, large database
- **Cons**: Limited metabolism/fm data

### 3. OpenFDA API (Free)
- **URL**: https://open.fda.gov/api/reference/
- **Cost**: Free
- **Data Quality**: Good for FDA label information
- **fm Data**: May have in drug labels, requires parsing
- **Rate Limits**: 240 requests per minute
- **Pros**: Free, official FDA data, no API key needed
- **Cons**: Requires parsing unstructured label text

### 4. ChEMBL API (Free)
- **URL**: https://www.ebi.ac.uk/chembl/api/data/
- **Cost**: Free
- **Data Quality**: Good for bioactivity data
- **fm Data**: Limited - primarily bioactivity, not metabolism
- **Rate Limits**: 5 requests per second
- **Pros**: Free, no API key needed
- **Cons**: Limited metabolism data

### 5. MyChem.info API (Free)
- **URL**: https://mychem.info/v1/
- **Cost**: Free
- **Data Quality**: Aggregates from multiple sources
- **fm Data**: May have some from DrugBank (via aggregation)
- **Rate Limits**: 1000 requests per day
- **Pros**: Free, aggregates multiple sources
- **Cons**: Rate limits, data quality varies

## Recommended Approach: Hybrid Strategy

### Phase 1: Free APIs (Immediate)
Use OpenFDA and PubChem to automate initial data collection

**OpenFDA Integration**:
- Query drug labels for metabolism information
- Parse Clinical Pharmacology sections
- Extract enzyme and fm data where available
- Cost: Free, no API key needed

**PubChem Integration**:
- Query for SMILES, molecular properties
- Get basic chemical information
- Cost: Free, no API key needed

### Phase 2: DrugBank API (If Budget Available)
If academic or corporate pricing is accessible, integrate DrugBank for comprehensive data

**DrugBank Integration**:
- Query for complete metabolism profiles
- Get fm data directly
- Get inhibition/induction data
- Cost: Paid subscription

## Implementation Plan

### Step 1: OpenFDA API Integration (Week 1)

**Create API Client**:
```python
# scripts/openfda_client.py
import requests

class OpenFDAClient:
    BASE_URL = "https://api.fda.gov/drug/label.json"
    
    def get_drug_label(self, drug_name):
        params = {"search": f'openfda.brand_name:"{drug_name}"'}
        response = requests.get(self.BASE_URL, params=params)
        return response.json()
    
    def extract_metabolism_data(self, label_data):
        # Parse Clinical Pharmacology section
        # Extract enzyme and fm information
        pass
```

**Test with Tier 1 Compounds**:
- Query OpenFDA for each Tier 1 compound
- Parse metabolism sections
- Extract available fm data
- Update JSON files automatically

**Expected Coverage**:
- OpenFDA may have fm data for 50-70% of compounds
- Manual curation still needed for gaps

### Step 2: PubChem API Integration (Week 1)

**Create API Client**:
```python
# scripts/pubchem_client.py
import requests

class PubChemClient:
    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    
    def get_smiles(self, drug_name):
        params = {"name": drug_name, "property": "IsomericSMILES"}
        response = requests.get(f"{self.BASE_URL}/compound/name/JSON", params=params)
        return response.json()
    
    def get_molecular_properties(self, drug_name):
        # Get molecular weight, logP, etc.
        pass
```

**Use For**:
- Fill missing SMILES in Kivo dataset
- Verify molecular properties
- Get additional chemical descriptors

### Step 3: DrugBank API Integration (If Budget Allows) (Week 2)

**Create API Client**:
```python
# scripts/drugbank_client.py
import requests

class DrugBankClient:
    BASE_URL = "https://go.drugbank.com/api/v1"
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def get_drug_metabolism(self, drug_name):
        response = requests.get(
            f"{self.BASE_URL}/drugs/{drug_name}",
            headers=self.headers
        )
        return response.json()
```

**Use For**:
- Comprehensive fm data
- Inhibition/induction data
- Transporter interactions

## Data Pipeline Architecture

```
┌─────────────────┐
│   User Input    │
│  (Drug Name)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API Orchestrator│
│  (scripts/api_   │
│   orchestrator)  │
└────────┬────────┘
         │
         ├──────────────────┬──────────────────┐
         │                  │                  │
         ▼                  ▼                  ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  OpenFDA    │   │  PubChem    │   │  DrugBank   │
│  API        │   │  API        │   │  API (opt)  │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         │
                         ▼
              ┌──────────────────┐
              │  Data Merger     │
              │  (combine data) │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  JSON Updater   │
              │  (update files) │
              └──────────────────┘
```

## Benefits of API Integration

**Immediate Benefits**:
- Automate data collection (saves 6-9 hours manual work)
- Scale to 100+ compounds easily
- Keep data current (automatic updates)
- Reduce human error

**Long-term Benefits**:
- On-demand data retrieval for new compounds
- Real-time updates from FDA labels
- Scalable to enterprise use
- Potential for SaaS product

## Cost Comparison

**Manual Curation**:
- Time: 6-9 hours for 30 compounds
- Cost: $0 (your time)
- Scalability: Poor (manual process)

**Free API Integration**:
- Time: 4-6 hours development (one-time)
- Cost: $0
- Scalability: Good (automated)
- Coverage: 50-70% automated

**DrugBank API Integration**:
- Time: 4-6 hours development (one-time)
- Cost: ~$500-2000/year (academic pricing)
- Scalability: Excellent
- Coverage: 90-95% automated

## Recommendation

**Start with OpenFDA API (Free)**:
1. Build OpenFDA client this week
2. Test with Tier 1 compounds
3. Automate what we can
4. Fill gaps manually

**Evaluate DrugBank API**:
1. Check if academic pricing available
2. Evaluate cost-benefit
3. If affordable, integrate for comprehensive coverage

## Next Steps

**Immediate**:
1. Create OpenFDA API client
2. Test with 2-3 compounds
3. Evaluate data quality
4. Decide on full implementation

**If Successful**:
1. Build full API integration
2. Replace manual curation workflow
3. Automate data updates
4. Scale to 100+ compounds

**Would you like me to start building the OpenFDA API client?**
