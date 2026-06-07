---
title: Service Runbook
---

# Modular DDI Service Runbook

## Overview
This document explains how to run the new modular services on the server. Each service is a standalone FastAPI app with its own dependencies and environment variables.

## Components
1. **ingestion-service** (`services/ingestion_service.py`)
2. **feature-service** (`services/feature_service.py`)
3. **prediction-service** (`services/prediction_service.py`)
4. **ui** (`ui/web/app.py`)

## Environment Variables
| Variable | Description | Default |
| --- | --- | --- |
| `PREDICTION_SERVICE_URL` | Base URL the UI uses to reach the prediction service | `http://localhost:8090` |
| `FEATURE_SERVICE_URL` | Base URL the UI uses to reach the feature service | `http://localhost:8091` |
| `UI_ROOT_PATH` | URL prefix when reverse-proxying the UI (e.g., `/ddi`) | *(empty)* |
| `SERVICE_PROJECT_ROOT` | Optional override for service config paths | repo root |

## Python Environment
All services rely on the repo’s requirements (`pip install -r requirements.txt`). For long-running service deployments, consider a dedicated virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Services

You can launch services in two ways:

1. **Typer CLI** – `python scripts/manage_services.py <prediction|feature|ingestion|ui>` runs a single service with the recommended env vars.
2. **tmux helper** – `./scripts/deploy_services.sh` spawns a tmux session (`ddi_services`) with prediction, feature, UI, and ingestion services in dedicated panes.

Manual uvicorn commands are below for reference.

## Offline Ingestion CLI

Use `python scripts/run_ingestion.py <fda|chembl|all>` (or `python scripts/manage_services.py ingest`) to refresh the data lake without hitting live APIs. Optional flags let you cap in-memory records (`--max-records`), memory budget in MB (`--max-mb`), force `--offline-only` mode for absolute air-gapped runs, redirect chunk output with `--output-dir`, and toggle curated manual seeds with `--include-manual-seeds/--no-include-manual-seeds`. The CLI parses ChEMBL drug mechanism exports and FDA SPL XMLs for enzyme mentions, writes the results under `data/warehouse/enzyme_annotations/`, and (by default) merges those annotations into `data/curated/*.json` so the UI can auto-populate substrate/inhibition fields. The CLI uses the same chunking defaults as the ingestion service, so it is safe to run on the 32 GB server.

Need to refresh only the high-priority manual seeds (Midazolam, Acetaminophen, Warfarin, Ketoconazole, Clarithromycin, Rifampin, etc.)? Run `python scripts/manage_services.py seed-annotations` (add `--output-dir` to target a staging area). Validation runs automatically; to lint edits without writing files (e.g., in CI), call `python scripts/manage_services.py validate-seeds`. Both commands ensure `manual_seed_annotations.json` stays consistent so the UI fetch endpoint and subsequent ingestion merges immediately pick up edits without touching the heavier pipelines.

Want to automate the curation entirely? Use the LLM helper commands: `python scripts/manage_services.py llm-generate-seed --compound <drug> --model-path <gguf>` prompts the local llama.cpp backend and writes the normalized JSON draft to `data/llm_curation/`, while `python scripts/manage_services.py llm-validate-all` runs the same schema linting over every curated and LLM-produced record before you persist with `seed-annotations`. Both commands honor the storage paths defined in `pipelines.settings.StoragePaths`, so you can keep generated files on faster scratch disks if needed.

### Prediction Service
```bash
uvicorn services.prediction_service:create_app --factory --host 0.0.0.0 --port 8090
```
- Responds with `/healthz`, `/metadata`, `/predict/enzyme`, `/predict/ddi`, `/recommend/validation`.
- Optional: set `PREDICTION_MODEL_VERSION` or similar env var when loading a new model artifact.

### Feature Service
```bash
uvicorn services.feature_service:create_app --factory --host 0.0.0.0 --port 8091
```
- Relies on curated JSON files under `data/curated/`. Ensure these are populated via ETL scripts.
- Exposes `/features/{compound_id}` and `/healthz`.

### Ingestion Service
```bash
uvicorn services.ingestion_service:create_app --factory --host 0.0.0.0 --port 8092
```
- Schedules offline ingestion runs via `/ingest/fda` and `/ingest/chembl` (FastAPI background tasks).
- Make sure `data/raw/fda/` and `data/raw/chembl/` contain the needed archives/TSVs before triggering.

### UI
```bash
PREDICTION_SERVICE_URL=http://localhost:8090 \
FEATURE_SERVICE_URL=http://localhost:8091 \
uvicorn ui.web.app:app --host 0.0.0.0 --port 8084
```
- Calls the prediction + feature services for API routes, and still supports `/api/fetch/drug` via `DataMerger`.
- Set `UI_ROOT_PATH=/ddi` (or similar) when serving the UI behind an nginx location block without a trailing slash so `/ddi/*` resolves correctly.

## Suggested Process Supervisor
For long-running deployments, use `systemd`, `tmux`, or `supervisord` to manage these processes. Example `tmux` layout:

1. `tmux new -s ddi`
2. Split into panes and start each service command above.

## Health Checks
- Prediction service: `curl http://localhost:8090/healthz`
- Feature service: `curl http://localhost:8091/healthz`
- Ingestion service: `curl http://localhost:8092/healthz`
- UI: `curl http://localhost:8084/`
- **Batch check**: `python scripts/check_services.py` (or `python scripts/manage_services.py check`) hits every endpoint above (plus the UI `/api/health`) concurrently and prints statuses.
- **Port status**: `python scripts/manage_services.py status` reports if the default service ports are already bound, useful before launching tmux/CLI sessions.

## Keeping Public URLs Stable

Use `scripts/sync_tailscale_routes.sh` any time you reload nginx, reboot the host, or notice `/pp`, `/ddi`, `/ovm`, or `/peds` dropping back to 404s. The helper script resets `tailscale serve` + `tailscale funnel` and reapplies all required mappings in one shot.

```bash
chmod +x scripts/sync_tailscale_routes.sh   # once
sudo scripts/sync_tailscale_routes.sh
```

The script expects Tailscale at `/usr/bin/tailscale` (override with `TAILSCALE_BIN=/path/to/tailscale`). It prints each Serve/Funnel mapping as it reapplies them and finishes by showing `tailscale funnel status` so you can verify `/`, `/ovm`, `/pp`, `/ddi`, and `/peds` are all registered.

### Optional systemd automation

`ops/systemd/sync-tailscale.service` + `.timer` can be copied into `/etc/systemd/system/` to run the script at boot and every 10 minutes automatically:

```bash
sudo cp ops/systemd/sync-tailscale.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sync-tailscale.timer
```

The timer triggers the service ~1 minute after boot and then every 10 minutes, ensuring the Serve/Funnel mappings are re-applied even if Tailscale resets or the box restarts.

### Optional watchdog

`scripts/check_public_urls.sh` curls `/ovm`, `/pp`, `/ddi`, `/peds` over the public domain. If any return non-200 it automatically reruns the sync script (with `sudo`). You can place it in cron/systemd, e.g.:

```bash
*/5 * * * * /home/martinvo/DDI/scripts/check_public_urls.sh >> /var/log/public-url-watchdog.log 2>&1
```

Set `TAILSCALE_SYNC_SCRIPT` or `TAILSCALE_BIN` env vars if the paths differ.

## Logs
Each service logs to stdout. For persistent logging, redirect output to files or configure `uvicorn --log-config`.

## Future Enhancements
- Add Celery/Dramatiq worker for long ingestion tasks.
- Containerize each service with Docker for easier orchestration.
- Add observability (Prometheus metrics, structured logging).
