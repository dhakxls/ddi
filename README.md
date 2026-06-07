# DDI Prediction MVP

Drug-Drug Interaction (DDI) prediction system for clinical trial risk assessment.

## Project Overview

This MVP aims to predict dominant enzymes responsible for drug metabolism and rank DDI risks to provide trial-relevant flags and validation experiment recommendations.

**Goal: Build a real MVP and run 1-2 pilots within the next year, targeting pilot partner identification by late fall.**

## Project Phases

### Phase 1: Data Curation (Current Focus)
- **COMPLETED**: Imported Kivo Sheet1 dataset with 100 well-characterized compounds
- Source from public regulatory (FDA, EMA) and literature databases
- Semi-manual process with consistent units and clear labeling rules
- **COMPLETED**: Integrate Kivo dataset schema with SMILES and molecular properties
- **COMPLETED**: Include DDI study data (AUC fold changes, inhibitor information)
- **NEXT**: Fill missing PK parameters using Imagand or manual curation
- **NEXT**: Standardize LogP at pH 7 (team decision for physiological relevance)

### Phase 2: Model Development
- **IN PROGRESS**: Integrate Shayne's dominant enzyme prediction training code
- DDI risk ranking system
- **PLANNED**: Evaluate Imagand diffusion model for feature extraction and data augmentation
- **PLANNED**: Use PCA to evaluate if diffusion model features improve predictions
- **PLANNED**: Integrate PyRosettaDDGfolding for binding affinity validation
- **PLANNED**: Combine rule-based (dominant enzyme) with ML predictions

### Phase 3: UI Development
- Simple interface for compound input
- Trial-relevant flag output
- Validation experiment recommendations
- Support SMILES input for rapid screening
- Show confidence levels for predictions

### Phase 4: Pilot Deployment
- Identify and engage pilot partners (target: late fall)
- Run 1-2 pilots within the next year
- Offer synthetic PK predictions as value-add service

## Project Structure

```
windsurf-project/
├── data/                    # Data storage
│   ├── raw/                # Raw data from sources
│   ├── curated/            # Curated compound data
│   └── schemas/            # Data schema definitions
├── models/                  # ML models
│   ├── enzyme_prediction/  # Dominant enzyme models
│   └── ddi_ranking/        # DDI risk ranking models
├── ui/                      # User interface
│   └── web/                # Web application
├── docs/                    # Documentation
│   ├── labeling_rules.md   # Data curation guidelines
│   └── curation_template.md # Data entry template
└── scripts/                 # Utility scripts
    ├── manage_services.py   # CLI to run modular FastAPI services and ingestion helpers
    ├── check_services.py    # Async health check across modular services
    └── run_ingestion.py     # Typer CLI to execute FDA/ChEMBL pipelines + curated enrichment
```

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Review labeling rules in `docs/labeling_rules.md`
3. Start data curation using updated templates in `docs/curation_template.md`
4. **NEW**: Review resource analysis in `docs/resource_analysis.md`
5. **NEW**: Use Kivo data loader: `python scripts/load_kivo_data.py`
6. **NEW**: Refresh offline datasets with `python scripts/run_ingestion.py <fda|chembl|all>` (or `python scripts/manage_services.py ingest`). Add `--output-dir /path/to/staging` to redirect chunked JSON outside `data/`, and use `--no-include-manual-seeds` if you want to skip the curated seed annotations for a fully automated run. The ingestion commands parse ChEMBL target exports + FDA SPL text to auto-populate substrate/inhibition data for curated compounds.
7. **NEW**: Quickly refresh the curated seed annotations (Midazolam, Acetaminophen, Warfarin, Ketoconazole, Clarithromycin, Rifampin, etc.) without running ingestion via `python scripts/manage_services.py seed-annotations [--output-dir /alt/data]`. Validation now runs automatically before writing files—use `python scripts/manage_services.py validate-seeds` to lint edits in CI or before committing.
8. **NEW**: Read `docs/service_runbook.md` for modular service deployment details
9. **NEW**: Use `python scripts/manage_services.py <service>` to launch prediction/feature/ingestion/UI servers locally
10. **NEW**: Run `python scripts/check_services.py` (or `python scripts/manage_services.py check`) to verify the four services respond before testing the UI
11. **NEW**: Run `python scripts/manage_services.py status` to see which default service ports are already occupied before launching anything
12. **NEW**: Smoke-test a real pair (e.g., acetaminophen vs warfarin or ketoconazole vs midazolam) with `python scripts/run_example_workflow.py --drug-a acetaminophen --drug-b warfarin`. The CLI fetches both drugs via the UI, optionally runs `/predict/enzyme`, and prints the `/predict/ddi` result in one go.
13. **NEW**: Automate manual curation with the LLM-driven workflow: run `python scripts/manage_services.py llm-generate-seed --compound midazolam --model-path models/llms/llama-7b/ggml-model-q4_0.gguf` (override paths as needed) to draft annotations under `data/llm_curation/`, then call `python scripts/manage_services.py llm-validate-all` to lint every curated + LLM seed before persisting.

## Modular Service Stack

The MVP now runs as four FastAPI services plus a shared UI:

| Service | Module | Default Port | Description |
| --- | --- | --- | --- |
| Ingestion | `services.ingestion_service` | 8092 | Triggers offline FDA/ChEMBL pipelines with background tasks |
| Feature | `services.feature_service` | 8091 | Serves curated compound feature slices from `data/curated/` |
| Prediction | `services.prediction_service` | 8090 | Hosts dominant-enzyme, DDI risk, and validation endpoints |
| UI | `ui/web/app.py` | 8084 | Thin front-end that calls the feature & prediction services and now pre-fills enzyme data using the offline annotations |

See `docs/service_runbook.md` for environment variables, commands, and health checks. The `scripts/manage_services.py` CLI wraps the uvicorn commands (e.g. `python scripts/manage_services.py prediction`).

### Deployment & Public Access Hardening

Homelab-wide URL automation now lives outside this repo in `/home/martinvo/homelab-routing/` so the DDI project stays focused on app code. That directory contains:

1. `sync_tailscale_routes.sh` – single source of truth that reapplies `/`, `/ovm`, `/pp`, `/ddi`, `/peds` mappings without downtime.
2. `sync-tailscale.service` + `.timer` (installed under `/etc/systemd/system/`) to run the script on boot and every 10 minutes.
3. `check_public_urls.sh` used by cron (`*/5 * * * *`) to curl each public path and auto-trigger the sync script if any fail.
4. `ovm-funnel-ensure.timer`/service now exec the same script every minute, so all automations converge on one implementation.

Keep the homelab-routing folder under source control separately if needed; no generated files for the other web apps are stored in this DDI repo.

## Recent Enhancements

### Kivo Dataset Integration (COMPLETED)
- **IMPORTED**: 100 compounds from Kivo Sheet1 dataset
- Updated data schema to include SMILES, InChIKey, molecular properties
- Added DDI study data fields (inhibitor_tested, AUC_fold_change)
- Enhanced PK parameters (clearance_L_h, dose_mg, AUC, Cmax)
- Created data loader for Kivo-format CSV files
- Updated curation template with new fields
- All compounds converted to JSON format in data/curated/

### Team Conversation Analysis
- Analyzed full team conversation for project context
- Documented technical decisions (LogP pH 7, unit standardization)
- Identified Shayne's dominant enzyme prediction code for integration
- Documented validation strategy (ketoconazole + CYP3A4 example)
- Created comprehensive project roadmap based on team discussions

### Imagand Diffusion Model
- Evaluated for synthetic PK data generation
- Team approved: Use for feature extraction with PCA evaluation
- If features don't improve predictions, revert to Plan A
- Planned integration in Phase 2

### PyRosettaDDGfolding
- Shayne's side project for binding affinity validation
- Takes ~3 minutes per prediction (algorithm, not ML)
- Shayne to revalidate and update parameters
- Planned for binding affinity validation in Phase 2

## Timeline

- **Phase 1**: Data curation (Q2-Q3 2026)
- **Phase 2**: Model development (Q3 2026)
- **Phase 3**: UI development (Q4 2026)
- **Phase 4**: Pilot deployment (Late Fall 2026)
