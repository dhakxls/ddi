# Resource Analysis for DDI Prediction Project

## Overview
Analysis of three new resources provided to refine the DDI prediction MVP scope.

## 1. Training Dataset Kivo(READ ME).csv

### Structure
This is a data template/schema file (not actual data) containing column definitions for pharmacokinetic data curation.

### Key Fields
**Molecular Properties:**
- inchi_key, smiles, molecular_weight_g_mol, logP, pKa, polar_surface_area_A2

**Enzyme/Metabolism Data:**
- dominant_enzyme (Primary metabolic enzyme from FDA Clinical Pharmacology Review)
- metabolism_type (CYP, UGT, Renal, or Mixed)
- fm_dominant (Fraction metabolized by dominant enzyme, 0-1 scale)
- secondary_enzyme (Second enzyme mentioned in metabolism section)

**PK Parameters:**
- dose_mg (Typical adult dose used in PK studies)
- AUC_ng_h_ml (Adult AUC from PK study)
- Cmax_ng_ml (Adult Cmax value)
- clearance_L_h (Systemic clearance converted to L/h)
- half_life_h (Elimination half life in hours)

**DDI Study Data:**
- inhibitor_tested (Drug used in DDI study)
- enzyme_inhibited (Enzyme inhibited in that study)
- AUC_fold_change (Increase in AUC during inhibitor study)
- data_source (Source of data)

### Alignment with Project
- **Highly relevant** - provides a concrete template for data curation
- Aligns well with our existing JSON schema
- Includes SMILES strings for molecular representation
- Contains actual DDI study data fields (AUC fold changes)
- Standardizes units (ng*h/mL, ng/mL, L/h, hours)

### Integration Recommendations
1. Use this schema as the primary template for data curation
2. Add SMILES and molecular properties to our existing compound schema
3. Incorporate the DDI study data structure (inhibitor_tested, AUC_fold_change)
4. Use the curation notes as quality control guidelines
5. Map fields to our existing JSON schema

## 2. Imagand (arxiv:2408.07636)

### Overview
"Drug Discovery SMILES-to-Pharmacokinetics Diffusion Models with Deep Molecular Understanding"

### Key Capabilities
- **SMILES-to-Pharmacokinetic (S2PK) diffusion model**
- Generates synthetic PK data from SMILES inputs
- Addresses data overlap sparsity in PK datasets
- Generates multiple PK target properties conditioned on SMILES
- Synthetic data closely resembles real data distributions
- Improves performance on downstream tasks

### Potential Applications for DDI Prediction
1. **Data Augmentation**: Generate synthetic PK data for compounds lacking real data
2. **Feature Extraction**: Use diffusion model to generate molecular representations
3. **Imputation**: Fill missing PK parameters in our curated dataset
4. **Prediction**: Predict PK properties for new compounds from SMILES
5. **Dataset Expansion**: Generate data for compounds beyond our 100 target list

### Integration Recommendations
**Phase 1 (Data Curation):**
- Use Imagand to generate synthetic PK data for compounds with missing parameters
- Validate synthetic data against known compounds
- Use as a data quality check (compare synthetic vs real data)

**Phase 2 (Model Development):**
- Integrate Imagand as a feature extractor for molecular representations
- Use synthetic data to train/enhance our DDI prediction models
- Combine with our curated dataset for larger training set

**Phase 3 (Pilot):**
- Offer synthetic PK predictions as a value-add service
- Use for rapid screening of new compounds before full curation

### Considerations
- Need to evaluate model accuracy on our target compounds
- Synthetic data should be clearly labeled vs real data
- Regulatory acceptance of synthetic PK data needs assessment
- Computational resources for running diffusion models

## 3. PyRosettaDDGfolding

### Overview
Tool for predicting DDG (change in folding free energy) upon mutation using PyRosetta.

### Components
- **Cleaner.py**: Prepares PDB files for PyRosetta
- **Relaxer.py**: Performs FastRelax protocol on structures
- **DDG_Calculator.py**: Calculates DDG for mutations

### Relevance to DDI Prediction
**Limited direct relevance** - this tool focuses on:
- Protein structure analysis
- Mutation effects on protein stability
- Not directly related to drug metabolism or enzyme interactions

### Potential Indirect Applications
1. **Enzyme Structure Analysis**: Could analyze CYP enzyme structures
2. **Mutation Impact**: Study how genetic variants affect enzyme function
3. **Binding Affinity**: Potentially predict drug-enzyme binding (with adaptation)
4. **Mechanistic Understanding**: Provide structural context for DDI mechanisms

### Integration Recommendations
**Low Priority for Initial MVP:**
- Not directly aligned with current DDI prediction focus
- Requires protein structures (PDB files) for CYP enzymes
- Significant computational overhead
- Would require substantial adaptation for drug-enzyme interactions

**Future Considerations:**
- If pilot partners express interest in genetic variants/pharmacogenomics
- For mechanistic studies of specific enzyme-drug pairs
- For understanding structural basis of DDI mechanisms

## Updated Project Scope Recommendations

### Immediate Changes (Phase 1)
1. **Adopt Kivo Schema**: Use the Kivo dataset schema as the primary curation template
2. **Add SMILES Support**: Incorporate SMILES strings and molecular properties into data schema
3. **Enhance DDI Data**: Include inhibitor_tested, enzyme_inhibited, AUC_fold_change fields
4. **Standardize Units**: Follow Kivo unit conventions (ng*h/mL, ng/mL, L/h)

### Medium-Term Enhancements (Phase 2)
1. **Integrate Imagand**: Evaluate and integrate Imagand for data augmentation
2. **Synthetic Data Generation**: Generate synthetic PK data for missing parameters
3. **Feature Engineering**: Use diffusion model outputs as molecular features
4. **Model Enhancement**: Train models on combined real + synthetic dataset

### Long-Term Considerations (Phase 3/Pilot)
1. **SMILES-Based Prediction**: Enable prediction from SMILES alone
2. **Rapid Screening**: Offer quick predictions for new compounds
3. **Structure-Based Analysis**: Consider PyRosetta for mechanistic studies if needed

## Priority Ranking
1. **High**: Integrate Kivo schema into data curation workflow
2. **High**: Evaluate Imagand for data augmentation
3. **Medium**: Add SMILES and molecular properties to models
4. **Low**: PyRosettaDDGfolding (defer unless specific need arises)

## Next Steps
1. Update data schema to align with Kivo template
2. Test Imagand on a subset of our target compounds
3. Create data loader for Kivo-format CSV files
4. Evaluate synthetic data quality against real data
