#!/usr/bin/env bash
#
# Simple watchdog: curl each public TailScale URL and optionally trigger
# sync_tailscale_routes.sh if any endpoint fails.

set -euo pipefail

TAILSCALE_SYNC_SCRIPT=${TAILSCALE_SYNC_SCRIPT:-/home/martinvo/DDI/scripts/sync_tailscale_routes.sh}
BASE_URL=${BASE_URL:-https://homelab.taild08007.ts.net}

if [[ ! -x ${TAILSCALE_SYNC_SCRIPT} ]]; then
    echo "error: sync script not executable at ${TAILSCALE_SYNC_SCRIPT}" >&2
    exit 1
fi

urls=(
    "ovm|${BASE_URL}/ovm/"
    "pp|${BASE_URL}/pp/"
    "ddi|${BASE_URL}/ddi/"
    "peds|${BASE_URL}/peds/"
)

missing=()
for entry in "${urls[@]}"; do
    name=${entry%%|*}
    url=${entry#*|}
    code=$(curl -sk --max-time 15 -o /dev/null -w "%{http_code}" "$url" || echo "000")
    if [[ ${code} != "200" ]]; then
        echo "[public-check] ${name} at ${url} returned ${code}" >&2
        missing+=("${name}")
    else
        echo "[public-check] ${name} OK"
    fi
done

if (( ${#missing[@]} == 0 )); then
    exit 0
fi

echo "[public-check] Detected failures (${missing[*]}), re-running tailscale sync" >&2
sudo --preserve-env=TAILSCALE_BIN ${TAILSCALE_SYNC_SCRIPT}
