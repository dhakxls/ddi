# Prototype Development Plan: Next Steps

## Current Status

**Working**
- ✓ Data loading: 100 compounds imported from Kivo Sheet1
- ✓ DDI risk ranking: Functional (tested with midazolam + ketoconazole)
- ✓ Command-line demo: Working (test_prototype.py)
- ✓ Core prediction logic: Substrate + inhibitor interactions identified

**Limitations**
- ⚠ Dominant enzyme prediction: Needs fraction metabolized (fm) data
- ⚠ Validation recommendations: Needs fm data
- ⚠ Web UI: Not yet tested with real data
- ⚠ Pediatric considerations: Not yet implemented
- ⚠ Missing PK parameters: Many compounds have incomplete data

## What Kivo Sheet1 Dataset Provides

### Immediate Value
- **100 real compounds** with SMILES strings and molecular properties
- **Enzyme coverage**: Diverse representation across major CYP enzymes
  - CYP3A4: 28 compounds
  - CYP2D6: 13 compounds
  - CYP2C9: 13 compounds
  - CYP2C19: 11 compounds
  - CYP1A2: 5 compounds
  - UGT enzymes: 8 compounds
  - Renal/Transporter: 8 compounds
- **Molecular descriptors**: logP, molecular weight, pKa, polar surface area
- **PK parameters**: Some compounds have clearance, half-life, dose, AUC, Cmax

### Development Value
1. **Testing Foundation**: Real compounds for model validation
2. **Training Data**: Can be used to train ML models (with fm data added)
3. **Coverage Assessment**: Shows which enzymes are well-represented vs. gaps
4. **Baseline Performance**: Establish baseline predictions before ML integration
5. **Pediatric Relevance**: Many compounds are used in pediatrics (antibiotics, antihistamines, asthma meds)

### Specific Compounds for Pediatric Scenario
From Kivo Sheet1, relevant for pediatric ADHD trial scenario:
- **Fluoxetine** (CYP2D6 inhibitor - common pediatric SSRI)
- **Sertraline** (CYP2C19 - pediatric SSRI)
- **Montelukast** (not in dataset, but similar compounds present)
- **Valproic Acid** (not in dataset, but anticonvulsants present)
- **Levetiracetam** (not in dataset, but renal compounds present)

## Next Steps to Flesh Out Prototype

### Phase 1: Complete Core Functionality (1-2 weeks)

**1. Add Fraction Metabolized (fm) Data**
- **Priority**: HIGH
- **Approach**: Manual curation from FDA labels and literature
- **Target**: Add fm data to 20-30 key compounds
- **Sources**:
  - FDA Clinical Pharmacology Reviews
  - DrugBank
  - Literature (PubMed)
- **Specific Compounds**:
  - Midazolam: CYP3A4 fm ~0.9
  - Fluoxetine: CYP2D6 fm ~0.6
  - Warfarin: CYP2C9 fm ~0.85
  - Metoprolol: CYP2D6 fm ~0.7
- **Outcome**: Enables dominant enzyme prediction and validation recommendations

**2. Test Web UI with Real Data**
- **Priority**: HIGH
- **Approach**: Start FastAPI server, test with Kivo compounds
- **Test Cases**:
  - Midazolam + Ketoconazole (should show MAJOR risk)
  - Warfarin + Fluconazole (should show MODERATE risk)
  - Metoprolol + Paroxetine (should show MODERATE risk)
- **Outcome**: Functional web interface for demonstration

**3. Handle Missing Data Gracefully**
- **Priority**: MEDIUM
- **Approach**: Add fallback logic for missing PK parameters
- **Implementation**:
  - If clearance missing: Use population average (e.g., 30 L/h for adults)
  - If half-life missing: Use therapeutic range
  - If fm missing: Use rule-based approach (substrate flag)
- **Outcome**: Models work with incomplete Kivo data

### Phase 2: Enhance with ML Models (2-3 weeks)

**4. Integrate Shayne's Dominant Enzyme Prediction Code**
- **Priority**: HIGH
- **Approach**: Get Shayne's training code, integrate with Kivo data
- **Requirements**:
  - Shayne provides code repository
  - Format Kivo data for training
  - Train model on compounds with fm data
  - Validate predictions against known data
- **Outcome**: ML-based dominant enzyme prediction

**5. Integrate Imagand for Feature Extraction**
- **Priority**: MEDIUM
- **Approach**: Use diffusion model to generate molecular features
- **Implementation**:
  - Run Imagand on Kivo SMILES strings
  - Extract molecular representations
  - Use PCA to evaluate feature value
  - Integrate if features improve predictions
- **Outcome**: Enhanced molecular features for ML models

**6. Implement PyRosettaDDGfolding for Validation**
- **Priority**: MEDIUM
- **Approach**: Use Shayne's binding affinity prediction
- **Implementation**:
  - Shayne revalidates parameters
  - Run binding predictions for high-risk pairs
  - Incorporate into validation recommendations
- **Outcome**: Mechanistic validation insights

### Phase 3: Pediatric-Specific Enhancements (2-3 weeks)

**7. Add Age-Stratified Analysis**
- **Priority**: HIGH (for pediatric focus)
- **Approach**: Account for developing CYP systems
- **Implementation**:
  - Add age groups: 6-12 years, 13-17 years
  - Adjust enzyme maturity factors (CYP2D6 develops slowly, CYP3A4 faster)
  - Modify risk scores based on age
  - Add pediatric-specific clinical implications
- **Outcome**: Pediatric-specific DDI predictions

**8. Add Weight-Based Dosing Considerations**
- **Priority**: HIGH (for pediatric focus)
- **Approach**: Account for weight-based dosing in children
- **Implementation**:
  - Add weight input field
  - Adjust clearance calculations for weight
  - Modify exposure predictions for pediatric PK
- **Outcome**: Pediatric-relevant dosing recommendations

**9. Add Pediatric-Specific Medications**
- **Priority**: MEDIUM
- **Approach**: Expand Kivo dataset with pediatric-specific compounds
- **Compounds to Add**:
  - Montelukast (asthma)
  - Cetirizine/Loratadine (allergies)
  - Valproic Acid (seizures)
  - Levetiracetam (seizures)
  - Amoxicillin/Azithromycin (antibiotics)
- **Outcome**: Comprehensive pediatric medication coverage

### Phase 4: Demonstration & Deployment (1-2 weeks)

**10. Create Comprehensive Demo**
- **Priority**: HIGH
- **Approach**: Multi-scenario demonstration
- **Scenarios**:
  - Scenario 1: Adult trial (original example)
  - Scenario 2: Pediatric ADHD trial (new focus)
  - Scenario 3: Drug development decision (compound selection)
  - Scenario 4: Regulatory submission (pediatric exclusivity)
- **Outcome**: Compelling demonstration for stakeholders

**11. Performance Optimization**
- **Priority**: MEDIUM
- **Approach**: Optimize for speed and scalability
- **Implementation**:
  - Cache compound data
  - Optimize database queries
  - Add batch processing for multiple compounds
- **Outcome**: Fast response times for user queries

**12. Documentation and Handoff**
- **Priority**: HIGH
- **Approach**: Complete documentation for team
- **Documentation**:
  - User guide for web UI
  - API documentation
  - Data curation guide
  - Model training guide
- **Outcome**: Team can use and extend the system

## How Kivo Sheet1 Specifically Helps Each Phase

### Phase 1: Core Functionality
- **Testing**: Real compounds to test DDI risk ranking (already working)
- **Baseline**: Establish baseline predictions before adding fm data
- **Coverage**: Shows which enzyme interactions are well-represented

### Phase 2: ML Models
- **Training Data**: 100 compounds for training dominant enzyme models
- **Feature Extraction**: SMILES strings for Imagand molecular features
- **Validation**: Known enzyme data to validate ML predictions

### Phase 3: Pediatric Enhancements
- **Relevance**: Many compounds used in pediatrics
- **Benchmark**: Adult data as baseline for pediatric adjustments
- **Expansion**: Foundation for adding pediatric-specific compounds

### Phase 4: Demonstration
- **Real Examples**: Actual compounds for demonstration scenarios
- **Diversity**: Multiple enzyme interactions for comprehensive demo
- **Credibility**: Real data adds credibility to demonstration

## Estimated Timeline

**Phase 1**: 1-2 weeks (immediate priority)
**Phase 2**: 2-3 weeks (after Phase 1)
**Phase 3**: 2-3 weeks (can overlap with Phase 2)
**Phase 4**: 1-2 weeks (final polish)

**Total**: 6-10 weeks to fully functional prototype

## Critical Path

**Must Have for MVP**:
1. Add fm data to 20-30 compounds (1 week)
2. Test web UI with real data (3 days)
3. Handle missing data gracefully (3 days)
4. Create basic demo (3 days)

**Nice to Have for Full Prototype**:
5. Integrate Shayne's ML models (2 weeks)
6. Add pediatric considerations (2 weeks)
7. Comprehensive demo (1 week)

## Success Metrics

**Technical**:
- [ ] Web UI loads and accepts compound names
- [ ] DDI predictions work with Kivo compounds
- [ ] Dominant enzyme prediction functional (with fm data)
- [ ] Validation recommendations generated
- [ ] Pediatric age-stratified analysis working

**User Experience**:
- [ ] Response time < 5 seconds per query
- [ ] Clear, actionable outputs
- [ ] Intuitive interface
- [ ] Handles errors gracefully

**Business Value**:
- [ ] Can demonstrate cost savings scenario
- [ ] Can show pediatric exclusivity value
- [ ] Can support compound selection decisions
- [ ] Ready for pilot partner discussions

## Next Immediate Actions

1. **This Week**: Add fm data to 10 key compounds (midazolam, ketoconazole, fluoxetine, warfarin, metoprolol, etc.)
2. **This Week**: Test web UI with these compounds
3. **Next Week**: Add fm data to 10 more compounds
4. **Next Week**: Create basic demo script

This plan leverages the Kivo Sheet1 dataset as the foundation while addressing its limitations (missing fm data) through targeted curation.
