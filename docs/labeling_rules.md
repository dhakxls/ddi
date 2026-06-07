# Data Curation Labeling Rules

## Purpose

Standardized rules for curating high-quality compound data from regulatory and literature sources.

## General Principles

1. **Consistency**: Use consistent units across all entries
2. **Traceability**: Document all data sources with URLs and access dates
3. **Completeness**: Fill all required fields; mark missing data as "NA"
4. **Accuracy**: Verify data against multiple sources when possible
5. **Standardization**: Use standardized nomenclature (INN, generic names)

## Compound Identification

### Required Fields
- **Compound Name**: Use INN (International Nonproprietary Name) when available
- **CAS Registry Number**: Include if available
- **DrugBank ID**: Include if available
- **FDA Application Number**: Include if available (NDA, ANDA, BLA)
- **Therapeutic Class**: ATC code preferred

### Naming Conventions
- Use generic names, not brand names
- Capitalize first letter only (e.g., "Warfarin" not "warfarin" or "WARFARIN")
- For salts, specify the salt form (e.g., "Warfarin sodium")

## Enzyme Data

### CYP Enzymes
Track the following CYP enzymes:
- CYP1A2, CYP2B6, CYP2C8, CYP2C9, CYP2C19, CYP2D6, CYP2E1, CYP3A4, CYP3A5

### Enzyme Interaction Types
- **Substrate**: Drug is metabolized by the enzyme
- **Inhibitor**: Drug inhibits the enzyme
  - Strong inhibitor: >80% decrease in clearance
  - Moderate inhibitor: 50-80% decrease in clearance
  - Weak inhibitor: <50% decrease in clearance
- **Inducer**: Drug induces the enzyme
  - Strong inducer: >5-fold increase in clearance
  - Moderate inducer: 2-5-fold increase in clearance
  - Weak inducer: <2-fold increase in clearance

### Units for Enzyme Data
- **Km**: μM (micromolar)
- **Vmax**: pmol/min/mg protein
- **IC50**: μM (micromolar)
- **Ki**: μM (micromolar)
- **CLint**: μL/min/mg protein
- **fm (fraction metabolized)**: Unitless (0-1)

## DDI Data

### DDI Risk Categories
- **Contraindicated**: Do not co-administer
- **Major**: Significant interaction, monitoring required
- **Moderate**: Interaction may occur, consider monitoring
- **Minor**: Minimal clinical significance

### DDI Evidence Sources
- FDA Drug Labels
- EMA SmPCs (Summary of Product Characteristics)
- Peer-reviewed literature
- Clinical trial data
- In vitro studies

## Data Sources

### Primary Sources
1. **FDA DailyMed**: https://dailymed.nlm.nih.gov/
2. **FDA Orange Book**: https://www.accessdata.fda.gov/scripts/cder/daf/
3. **EMA EPAR**: https://www.ema.europa.eu/en/medicines/human/EPAR
4. **DrugBank**: https://go.drugbank.com/
5. **PubChem**: https://pubchem.ncbi.nlm.nih.gov/

### Literature Sources
- PubMed
- Google Scholar
- Clinical Pharmacology & Therapeutics
- Drug Metabolism and Disposition

## Quality Control

### Validation Checks
1. Verify CAS number format (XXX-XX-X)
2. Check enzyme name spelling
3. Verify unit consistency
4. Cross-reference with at least 2 sources for critical data
5. Flag discrepancies for manual review

### Data Entry Protocol
1. Enter data from primary source
2. Cross-check with secondary source
3. Resolve discrepancies
4. Document any assumptions
5. Submit for peer review

## Missing Data Handling
- Use "NA" for truly missing data
- Use "Not reported" if data not available in source
- Use "Not applicable" if field not relevant to compound
- Add comments explaining missing data when possible

## Version Control
- Track data changes with timestamps
- Document source of each data point
- Maintain change log for all modifications
