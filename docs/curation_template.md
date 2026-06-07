# Compound Data Curation Template (Updated with Kivo Schema)

## Compound Identification

| Field | Value | Source | Notes |
|-------|-------|--------|-------|
| Compound Name (INN) | | | |
| CAS Number | | | |
| DrugBank ID | | | |
| FDA Application Number | | | |
| ATC Code | | | |
| Therapeutic Class | | | |

## Molecular Properties (NEW - from Kivo schema)

| Field | Value | Source | Notes |
|-------|-------|--------|-------|
| SMILES | | PubChem/ChEMBL | Stereochemistry sometimes missing |
| InChIKey | | PubChem | Occasionally multiple entries for salts |
| Molecular Weight (g/mol) | | PubChem | Check units are g/mol |
| logP | | PubChem/ChEMBL | Choose experimental if possible |
| pKa | | PubChem/literature | Some drugs have multiple pKa values |
| Polar Surface Area (Å²) | | PubChem | May be missing for some compounds |
| Metabolism Type | | FDA | CYP, UGT, Renal, or Mixed |

## Enzyme Substrate Data

| Enzyme | Substrate? | Km (μM) | Vmax (pmol/min/mg) | CLint (μL/min/mg) | fm | Source | Notes |
|--------|------------|---------|-------------------|-------------------|-----|--------|-------|
| CYP1A2 | | | | | | | |
| CYP2B6 | | | | | | | |
| CYP2C8 | | | | | | | |
| CYP2C9 | | | | | | | |
| CYP2C19 | | | | | | | |
| CYP2D6 | | | | | | | |
| CYP2E1 | | | | | | | |
| CYP3A4 | | | | | | | |
| CYP3A5 | | | | | | | |

## Enzyme Inhibition Data

| Enzyme | Inhibitor? | Type (Strong/Moderate/Weak) | IC50 (μM) | Ki (μM) | Source | Notes |
|--------|------------|-----------------------------|----------|---------|--------|-------|
| CYP1A2 | | | | | | |
| CYP2B6 | | | | | | |
| CYP2C8 | | | | | | |
| CYP2C9 | | | | | | |
| CYP2C19 | | | | | | |
| CYP2D6 | | | | | | |
| CYP2E1 | | | | | | |
| CYP3A4 | | | | | | |
| CYP3A5 | | | | | | |

## Enzyme Induction Data

| Enzyme | Inducer? | Type (Strong/Moderate/Weak) | Fold Change | Source | Notes |
|--------|----------|-----------------------------|-------------|--------|-------|
| CYP1A2 | | | | | |
| CYP2B6 | | | | | |
| CYP2C8 | | | | | |
| CYP2C9 | | | | | |
| CYP2C19 | | | | | |
| CYP2D6 | | | | | |
| CYP2E1 | | | | | |
| CYP3A4 | | | | | |
| CYP3A5 | | | | | |

## Known DDIs

| Interacting Drug | DDI Risk Category | Clinical Effect | Evidence Source | Notes |
|------------------|-------------------|-----------------|-----------------|-------|
| | | | | |
| | | | | |
| | | | | |

## Clinical Pharmacokinetics

| Parameter | Value | Unit | Source | Notes |
|-----------|-------|------|--------|-------|
| Oral Bioavailability | | % | | |
| Protein Binding | | % | | |
| Volume of Distribution | | L/kg | | |
| Clearance | | mL/min/kg | | |
| Clearance | | L/h | NEW: Systemic clearance |
| Half-life | | hours | | |
| Dose | | mg | NEW: Typical adult dose |
| AUC | | ng*h/mL | NEW: Adult AUC |
| Cmax | | ng/mL | NEW: Adult Cmax |
| Major Metabolites | | | | |

## DDI Study Data (NEW - from Kivo schema)

| Field | Value | Source | Notes |
|-------|-------|--------|-------|
| Inhibitor Tested | | | Drug used in DDI study |
| Enzyme Inhibited | | | Enzyme inhibited in study |
| AUC Fold Change | | | e.g., 3.2 for 3.2x increase |
| Cmax Fold Change | | | |
| Study Design | | | |
| Study Source | | | |

## Curation Metadata

| Field | Value |
|-------|-------|
| Curator Name | |
| Curation Date | |
| Primary Data Source | |
| Secondary Data Source | |
| Data Quality Rating (A/B/C) | |
| Peer Reviewer | |
| Peer Review Date | |
| Comments/Issues | |

## Data Quality Rating Scale
- **A**: High confidence - data from primary regulatory source, cross-verified
- **B**: Medium confidence - data from literature or single regulatory source
- **C**: Low confidence - data from limited sources or with discrepancies
