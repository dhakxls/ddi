# Team Conversation Analysis

## Project Context from DDI Team Conversation

### Core Project Vision (Lance)
Build a **real MVP** and run **1-2 pilots within the next year**.

### Project Phases

**Phase 1: Data Curation**
- Curate high-quality dataset for **100 well-characterized compounds**
- Source from public regulatory (FDA, EMA) and literature databases
- Semi-manual process with **consistent units** and clear labeling rules
- Target pilot partners by **late fall**

**Phase 2: Model Development**
- Dominant enzyme prediction model
- DDI risk ranking system

**Phase 3: UI Development**
- Simple interface for compound input
- Trial-relevant flag output
- Validation experiment recommendations

**Phase 4: Pilot Deployment**
- Identify and engage pilot partners
- Run 1-2 pilots within the next year

### Team Roles and Contributions

**Lance (Project Lead)**
- Project vision and timeline
- Data curation oversight
- Unit standardization focus
- Validation requirements

**Shayne (ML/Technical)**
- Has training code for dominant enzyme prediction
- Working on data scraping from PubChem and other sources
- Provided PyRosettaDDGfolding for binding affinity prediction
- Suggested Imagand diffusion model for data aggregation
- Moved to new department, busy but committed

**Martin (Data Curation)**
- Data curation lead
- Email coordination
- Validation data sourcing

### Technical Decisions Discussed

**Data Sources**
- PubChem for SMILES, molecular properties
- FDA Clinical Pharmacology Reviews for enzyme data
- SwissADME for additional properties
- Literature sources for DDI studies

**Feature Engineering**
- LogP standardization: Discussed pH 7 vs pH 9, decided on **pH 7** (closer to physiology)
- Concern about LogP variance/noise in experimental data
- Considered XLogP3 for consistency but decided experimental data is better

**Validation Strategy**
- Need examples of user input and expected output
- Want validation data to double-check work
- Shayne has validation script for PyRosettaDDGfolding
- Need compound + enzyme + binding affinity examples

**PyRosettaDDGfolding Integration**
- Shayne's side project for binding affinity prediction
- Uses Rosetta for protein-ligand binding
- Takes ~3 minutes to run (not ML model, algorithm)
- Can preprocess data
- Shayne to revalidate and update parameters

**Imagand Diffusion Model**
- Lance suggested using for data aggregation
- Shayne approved: Use for as many features as possible, then PCA to see if features help
- If features don't help, revert to Plan A

### Data Curation Guidelines from Conversation

**Units Standardization**
- Watch units carefully (Lance emphasized)
- Clearance: Convert to L/h (often reported as mL/min)
- If no weight for clearance, divide by 70kg
- AUC: Convert to ng*h/mL (sometimes reported as ug*h/L)
- Cmax: Convert to ng/mL

**Data Quality**
- Consistent units across all compounds
- Clear labeling rules
- Semi-manual curation process
- Multiple sources may conflict - need resolution strategy

### Kivo Dataset Analysis

**Dataset Structure**
- 100 compounds in Training Dataset Kivo(Sheet1).csv
- Fields: drug_name, Owner, dominant_enzyme, Internal_ID, inchi_key, smiles, molecular_weight, logP, pKa, polar_surface_area, metabolism_type, fm_dominant, secondary_enzyme, dose_mg, AUC_ng_h_ml, Cmax_ng_ml, clearance_L_h_kg, half_life_h, inhibitor_tested_SMILES, enzyme_inhibited, AUC_fold_change, data_source

**Data Completeness**
- Some rows have complete data (e.g., Midazolam)
- Many rows have missing PK parameters
- SMILES and molecular properties available for most compounds
- DDI study data sparse (mostly empty)

**Owner Distribution**
- Lance: CYP3A4 and CYP2D6 compounds (rows 1-36)
- Martin: CYP2C9, CYP2C19, UGT compounds (rows 37-67)
- Shayne: Remaining compounds including CYP3A4, CYP1A2, Renal, Transporter (rows 68-100)

### Project Refinement Recommendations

**Immediate Actions**
1. Import Kivo Sheet1 dataset (100 compounds) - provides solid foundation
2. Use Shayne's dominant enzyme prediction code as baseline
3. Implement data loader for Kivo dataset
4. Standardize LogP at pH 7 as discussed
5. Set up validation examples for model testing

**Phase 1 Enhancements**
- Start with Kivo dataset as base (100 compounds)
- Fill missing PK parameters using Imagand or manual curation
- Add more compounds from regulatory sources beyond initial 100
- Implement unit conversion functions for consistency

**Phase 2 Enhancements**
- Integrate Imagand for feature extraction and data augmentation
- Use PCA to evaluate if diffusion model features improve predictions
- Implement Shayne's PyRosettaDDGfolding for binding affinity validation
- Combine rule-based (dominant enzyme) with ML predictions

**Phase 3 Enhancements**
- UI should support both manual entry and SMILES input
- Include trial-relevant flags based on DDI risk
- Provide validation experiment recommendations
- Show confidence levels for predictions

**Validation Strategy**
- Create gold standard dataset with known DDI pairs
- Use ketoconazole + CYP3A4 as validation example (discussed in convo)
- Compare model outputs to known clinical DDI studies
- Implement cross-validation on curated dataset

### Timeline Considerations

**Current Status**
- Kivo dataset available (100 compounds)
- Shayne has training code ready
- Data scraping partially done
- Need to coordinate schedules for development

**Critical Path**
1. Data curation (bottleneck - requires manual work)
2. Model development (Shayne has code, needs integration)
3. UI development (can proceed in parallel)
4. Pilot partner identification (target: late fall)

### Risk Factors

**Data Quality**
- Variance in experimental data (LogP, PK parameters)
- Conflicting sources need resolution
- Manual curation time-intensive

**Coordination**
- Shayne moved to new department, busy
- Need to coordinate schedules for development
- Martin needs validation data sources

**Technical**
- PyRosettaDDGfolding runtime (3 minutes per prediction)
- Imagand integration complexity
- Model accuracy validation

### Success Metrics

**Phase 1**
- 100 compounds curated with consistent units
- Data schema validated
- Validation examples ready

**Phase 2**
- Dominant enzyme prediction accuracy > 80%
- DDI risk ranking correlates with clinical outcomes
- Model validated against gold standard

**Phase 3**
- Functional UI deployed
- Trial-relevant flags working
- Validation recommendations generated

**Phase 4**
- 1-2 pilot partners engaged
- Pilot studies completed
- Feedback incorporated

### Next Steps

1. **Import Kivo Sheet1 dataset** - create loader script
2. **Meet with team** - coordinate development schedule
3. **Set up validation examples** - ketoconazole + CYP3A4 pair
4. **Integrate Shayne's code** - baseline dominant enzyme model
5. **Begin data curation** - fill missing parameters in Kivo dataset
