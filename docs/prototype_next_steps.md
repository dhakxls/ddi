# Working Prototype Next Steps

## Current Status

**Completed**
- 100 compounds imported from Kivo Sheet1 dataset
- Data schema updated with SMILES, molecular properties, DDI study data
- Baseline models created (dominant_enzyme_model.py, ddi_risk_model.py)
- UI created (app.py, index.html)
- Validation engine created (validation_engine.py)

**What We Have**
- Data: 100 compounds with enzyme data, some PK parameters, SMILES
- Models: Rule-based dominant enzyme prediction, DDI risk ranking
- UI: FastAPI web application with HTML interface
- Validation: Experiment recommendation engine

## Critical Next Steps for Working Prototype

### 1. Test Models with Kivo Data (HIGH PRIORITY)

**Why**: Current models were created with example data, need to work with actual Kivo dataset

**Tasks**:
- Load a few Kivo compounds into the dominant enzyme model
- Test if the model correctly identifies dominant enzymes from the dataset
- Verify enzyme data mapping (CYP3A4, CYP2D6, etc.) works correctly
- Test DDI risk ranking with actual compound pairs from the dataset

**Expected Outcome**: Models can process Kivo compounds and produce reasonable predictions

### 2. Create Validation Example (HIGH PRIORITY)

**Why**: Team discussed ketoconazole + CYP3A4 as validation example; need concrete test case

**Tasks**:
- Create ketoconazole compound entry with CYP3A4 inhibition data
- Create midazolam compound entry (CYP3A4 substrate)
- Test DDI prediction: ketoconazole + midazolam should show high risk
- Verify AUC fold change predictions align with known clinical data

**Expected Outcome**: Concrete validation case that demonstrates system works

### 3. Test End-to-End Web UI (HIGH PRIORITY)

**Why**: Need to demonstrate working prototype through UI

**Tasks**:
- Start FastAPI server: `uvicorn ui.web.app:app --reload`
- Load web interface in browser
- Test dominant enzyme prediction with a Kivo compound (e.g., midazolam)
- Test DDI risk ranking with two compounds (e.g., ketoconazole + midazolam)
- Test validation recommendations
- Verify outputs are reasonable and formatted correctly

**Expected Outcome**: Functional web UI that processes real compounds

### 4. Handle Missing Data Gracefully (MEDIUM PRIORITY)

**Why**: Kivo dataset has many missing PK parameters; models shouldn't crash

**Tasks**:
- Identify which PK parameters are missing in Kivo dataset
- Update models to handle None/missing values
- Add fallback logic for missing data (e.g., use population averages)
- Test models with compounds that have missing data

**Expected Outcome**: Models work even with incomplete data

### 5. Create Demo Script (HIGH PRIORITY)

**Why**: Need automated way to demonstrate prototype functionality

**Tasks**:
- Create script that loads 2-3 representative compounds
- Runs dominant enzyme prediction
- Runs DDI risk ranking
- Runs validation recommendations
- Outputs clear, formatted results
- Can be run to quickly demonstrate system

**Expected Outcome**: One-command demo that shows all features

## Recommended Prototype Flow

### Minimal Viable Prototype (MVP)

**Input**: Two drug names from Kivo dataset
**Process**:
1. Load compound data from JSON files
2. Predict dominant enzymes for each drug
3. Calculate DDI risk based on enzyme interactions
4. Generate validation experiment recommendations
5. Display results with clinical implications

**Output**: 
- Dominant enzyme predictions with confidence
- DDI risk category (low/moderate/high)
- Clinical implications
- Recommended validation experiments
- Estimated costs and timelines

### Example Use Case

**User Input**: 
- Drug A: Midazolam
- Drug B: Ketoconazole

**System Output**:
- Midazolam: Dominant enzyme CYP3A4 (confidence: high)
- Ketoconazole: Strong CYP3A4 inhibitor
- DDI Risk: HIGH (AUC fold change expected: 3-5x)
- Clinical Implications: Significant increase in midazolam exposure, consider dose reduction
- Validation Recommendations: In vitro CYP3A4 inhibition assay, clinical DDI study
- Priority: HIGH
- Estimated Cost: $50-100K
- Timeline: 3-6 months

## Technical Implementation Steps

### Step 1: Test Data Loading
```python
# Load a few Kivo compounds
from pathlib import Path
import json

curated_dir = Path("data/curated")
compounds = []
for file in ["midazolam.json", "ketoconazole.json", "warfarin.json"]:
    with open(curated_dir / file) as f:
        compounds.append(json.load(f))
```

### Step 2: Test Dominant Enzyme Model
```python
from models.enzyme_prediction.dominant_enzyme_model import DominantEnzymePredictor

predictor = DominantEnzymePredictor()
for compound in compounds:
    result = predictor.predict_dominant_enzyme(compound["enzyme_data"])
    print(f"{compound['compound_name']}: {result.dominant_enzyme}")
```

### Step 3: Test DDI Risk Model
```python
from models.ddi_ranking.ddi_risk_model import DDIRiskRanker

ranker = DDIRiskRanker()
result = ranker.rank_ddi_risk(compounds[0], compounds[1])
print(f"DDI Risk: {result.risk_category}")
print(f"Clinical Implications: {result.clinical_implications}")
```

### Step 4: Test Validation Engine
```python
from models.validation_recommendation.validation_engine import ValidationRecommendationEngine

engine = ValidationRecommendationEngine()
recommendations = engine.generate_recommendations(compounds[0], compounds[1], result)
for rec in recommendations:
    print(f"{rec.type}: {rec.priority} - {rec.rationale}")
```

### Step 5: Test Web UI
```bash
# Start server
uvicorn ui.web.app:app --reload --port 8000

# Open browser to http://localhost:8000
# Test with compound names from Kivo dataset
```

## Success Criteria for Working Prototype

**Must Have**:
- [ ] Can load Kivo compounds from JSON files
- [ ] Dominant enzyme model produces reasonable predictions
- [ ] DDI risk model calculates risk scores correctly
- [ ] Validation engine generates recommendations
- [ ] Web UI loads and accepts input
- [ ] Web UI displays results correctly
- [ ] At least one concrete validation case works (ketoconazole + midazolam)
- [ ] System handles missing data without crashing

**Nice to Have**:
- [ ] Confidence scores for predictions
- [ ] Multiple validation examples
- [ ] SMILES input support
- [ ] Batch processing capability
- [ ] Export results to PDF/CSV

## Timeline Estimate

**Immediate (This Week)**:
- Test data loading
- Test models with Kivo data
- Create validation example

**Short-term (Next Week)**:
- Handle missing data
- Test web UI end-to-end
- Create demo script

**Medium-term (2-3 Weeks)**:
- Refine based on testing
- Add more validation cases
- Prepare for team demo

## Dependencies on Team Members

**Shayne**:
- Provide dominant enzyme prediction training code
- Revalidate PyRosettaDDGfolding parameters
- Integration guidance for ML models

**Martin**:
- Provide additional validation data sources
- Help with data quality checks
- Feedback on clinical relevance

**Lance**:
- Coordinate team meetings
- Provide pilot partner criteria
- Feedback on prototype direction

## Risk Mitigation

**If models don't work with Kivo data**:
- Fall back to rule-based approach using enzyme data directly
- Use simple heuristics for DDI risk (substrate + inhibitor = high risk)

**If web UI has issues**:
- Create command-line interface as backup
- Provide simple Python script for demonstration

**If validation examples fail**:
- Use known clinical DDI pairs from literature
- Create synthetic validation cases based on known pharmacology

## Next Immediate Action

**Priority 1**: Test dominant enzyme model with midazolam and ketoconazole from Kivo dataset

This will immediately show if the current models can work with the actual data and provide a concrete validation case for the prototype.
