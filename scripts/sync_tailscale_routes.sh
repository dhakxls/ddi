#!/usr/bin/env bash
#
# Recreate the Tailscale Serve + Funnel mappings required for all public apps.
# This prevents /ovm, /pp, /ddi, and /peds from falling back to the default handler
# whenever Tailscale drops per-path configuration (e.g., after nginx reloads or OS restarts).

set -euo pipefail

TAILSCALE_BIN=${TAILSCALE_BIN:-/usr/bin/tailscale}

if [[ ! -x ${TAILSCALE_BIN} ]]; then
    echo "error: tailscale binary not found at ${TAILSCALE_BIN}" >&2
    exit 1
fi

announce() {
    echo "[sync-tailscale] $*"
}

# Ordered list of path -> backend mappings. The first entry is the root handler.
declare -a PATHS=(
    "/ http://127.0.0.1:8099"
    "/ovm http://127.0.0.1:8085/ovm/"
    "/pp http://127.0.0.1:8085/pp/"
    "/ddi http://127.0.0.1:8085/ddi/"
    "/peds http://127.0.0.1:9075/peds"
)

announce "Resetting existing Serve/Funnel mappings"
"${TAILSCALE_BIN}" serve reset
"${TAILSCALE_BIN}" funnel reset

announce "Re-applying Serve mappings"
for entry in "${PATHS[@]}"; do
    path=${entry%% *}
    target=${entry#* }
    if [[ ${path} == "/" ]]; then
        "${TAILSCALE_BIN}" serve --bg --https=443 "${target}"
    else
        "${TAILSCALE_BIN}" serve --bg --https=443 --set-path "${path}" "${target}"
    fi
    announce "Serve: ${path} -> ${target}"
done

announce "Re-applying Funnel mappings"
for entry in "${PATHS[@]}"; do
    path=${entry%% *}
    target=${entry#* }
    if [[ ${path} == "/" ]]; then
        "${TAILSCALE_BIN}" funnel --bg --set-path "/" "${target}"
    else
        "${TAILSCALE_BIN}" funnel --bg --set-path "${path}" "${target}"
    fi
    announce "Funnel: ${path} -> ${target}"
done

announce "Current status:"
"${TAILSCALE_BIN}" funnel status
