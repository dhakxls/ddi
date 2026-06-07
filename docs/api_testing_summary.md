# API Testing Summary - Free Drug Database Evaluation

## Objective
Evaluate free/open source drug database APIs to determine if they provide fm (fraction metabolized) data and other metabolism information not available in OpenFDA and PubChem.

## APIs Tested

### 1. OpenFDA API ✓ WORKING
- **URL**: https://api.fda.gov/drug/label.json
- **Cost**: Free
- **Data Quality**: Good for FDA label information
- **Results**:
  - Successfully retrieves FDA labels
  - Detects enzyme mentions (CYP2D6, CYP2C9, CYP3A4)
  - **fm Data**: Not available in structured format
  - Rate limit: 240 requests/minute (respected)

### 2. PubChem API ✓ WORKING
- **URL**: https://pubchem.ncbi.nlm.nih.gov/rest/pug
- **Cost**: Free
- **Data Quality**: Excellent for chemical properties
- **Results**:
  - **SMILES**: 100% coverage (10/10 compounds tested)
  - **Molecular Weight**: 100% coverage (10/10 compounds tested)
  - **fm Data**: Not available
  - Rate limit: 5 requests/second (respected)

### 3. ChEMBL API ✗ NO USEFUL DATA
- **URL**: https://www.ebi.ac.uk/chembl/api/data
- **Cost**: Free
- **Data Quality**: Good for bioactivity data
- **Results**:
  - Successfully connects to API
  - **Enzyme Targets**: 0% coverage (0/3 compounds tested)
  - **fm Data**: Not available
  - **Issue**: Bioactivity data doesn't include metabolism/fm information

### 4. MyChem.info API ✗ SERVICE UNAVAILABLE
- **URL**: https://mychem.info/v1
- **Cost**: Free
- **Data Quality**: Unknown (aggregates multiple sources including DrugBank)
- **Results**:
  - **404 Errors**: 100% (3/3 compounds tested)
  - **Issue**: API endpoint may be down or changed
  - Could not evaluate data quality

## Test Compounds
- Midazolam
- Fluoxetine
- Warfarin

## Coverage Results

| Data Type | OpenFDA | PubChem | ChEMBL | MyChem.info | Overall |
|-----------|---------|---------|--------|-------------|---------|
| SMILES | 0% | 100% | 0% | 0% | 100% |
| Molecular Weight | 0% | 100% | 0% | 0% | 100% |
| Enzyme Mentions | 67% | 0% | 0% | 0% | 67% |
| fm Data | 0% | 0% | 0% | 0% | 0% |

## Key Findings

### What Works
- **PubChem**: Excellent for chemical properties (SMILES, MW) - 100% coverage
- **OpenFDA**: Good for enzyme detection in labels - 67% coverage

### What Doesn't Work
- **fm Data**: Not available in any free API in structured format
- **ChEMBL**: Bioactivity data doesn't include metabolism information
- **MyChem.info**: Service unavailable (404 errors)

## Conclusion

**Free APIs do not provide fm data in structured format.**

The fraction metabolized (fm) data required for dominant enzyme prediction is not available from:
- OpenFDA (FDA labels mention enzymes but don't provide fm values)
- PubChem (focuses on chemical properties, not metabolism)
- ChEMBL (focuses on bioactivity, not metabolism)
- MyChem.info (service unavailable)

## Recommendation

**Proceed with manual curation for fm data.**

### Rationale
1. Free APIs cannot provide fm data in structured format
2. Manual curation of 20-30 compounds is faster (2-3 hours) than continuing API development
3. Chemical properties (SMILES, MW) are 100% automated via PubChem
4. Enzyme detection is 67% automated via OpenFDA

### Next Steps
1. Create script to update JSON files with API-derived SMILES and MW
2. Manually add fm data to 20-30 key compounds from FDA Clinical Pharmacology Reviews
3. Use the curated data to enable dominant enzyme prediction
4. Proceed with prototype testing

### Alternative Considered (Rejected)
- **DrugBank API**: Paid subscription ($500-2000/year) - would provide fm data but adds cost and time for setup
- **Decision**: Manual curation is faster and free for initial prototype

## Cost-Benefit Analysis

### Manual Curation Approach
- **Time**: 2-3 hours for 20-30 compounds
- **Cost**: $0
- **Coverage**: 100% for curated compounds
- **Timeline**: Can start immediately

### DrugBank API Approach
- **Time**: 4-6 hours development + setup
- **Cost**: $500-2000/year
- **Coverage**: 90-95% automated
- **Timeline**: 1-2 weeks to implement and test

**Decision**: Manual curation for MVP, consider DrugBank for production scaling.

## Data Sources for Manual Curation

### FDA Clinical Pharmacology Reviews (Best Source)
- URL: https://www.accessdata.fda.gov/scripts/cder/daf/
- Search drug name → Find "Clinical Pharmacology and Biopharmaceutics Review(s)"
- Search within document for "fraction metabolized" or "fm"

### DrugBank (Secondary Source)
- URL: https://go.drugbank.com/
- Search drug name → Check "Pharmacology" → "Metabolism" section

### Literature (Tertiary Source)
- PubMed search: "[drug name] fraction metabolized [enzyme]"
- Review articles on drug metabolism

## Priority Compounds for Manual Curation

### Tier 1 (Critical for Testing)
1. Midazolam - CYP3A4
2. Ketoconazole - CYP3A4 (inhibitor)
3. Fluoxetine - CYP2D6
4. Warfarin - CYP2C9
5. Metoprolol - CYP2D6
6. Propranolol - CYP2D6
7. Diazepam - CYP2C19
8. Omeprazole - CYP2C19
9. Phenytoin - CYP2C9
10. Ibuprofen - CYP2C9

### Tier 2 (High-Value from Kivo)
11. Simvastatin - CYP3A4
12. Atorvastatin - CYP3A4
13. Sertraline - CYP2C19
14. Escitalopram - CYP2C19
15. Losartan - CYP2C9
16. Diclofenac - CYP2C9
17. Venlafaxine - CYP2D6
18. Paroxetine - CYP2D6
19. Codeine - CYP2D6
20. Tramadol - CYP2D6

## Success Criteria

After manual curation:
- [ ] 20 Tier 1 compounds have fm data
- [ ] Dominant enzyme prediction functional
- [ ] Validation recommendations functional
- [ ] Prototype test script passes all tests
- [ ] Ready for web UI testing

## Timeline Estimate

- **Week 1**: Manual curation of 20 compounds (2-3 hours)
- **Week 1**: Update JSON files with API + manual data (1 hour)
- **Week 1**: Re-run test_prototype.py (30 min)
- **Week 1**: Test web UI (1 hour)

**Total**: ~6 hours to functional prototype with fm data
