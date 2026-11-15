#!/usr/bin/env bash
# Load _config/reference/canon/*.md into the Nexus collection `megajam_canon`.
# Needs the local model host (Lemonade, embeddings) and the GPU: run `gpu-preflight` first and
# never run it while the editor or another GPU job is up. The hub runs this after merges.
#
# Depends on Nexus `backend/scripts/ingest_unreal_canon.py --corpus-dir`, added by a separate
# Nexus ticket. If that PR is not merged yet the script exits with an "unrecognized arguments" error;
# the script itself is correct and needs no change once Nexus has it.
#
# Extra arguments pass through, e.g. `scripts/canon_ingest.sh --dry-run` (count and chunk, embed nothing).
set -euo pipefail
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
canon_backend="${MEGAJAM_CANON_BACKEND:-${HOME}/Projects/nexus/backend}"
canon_python="${MEGAJAM_CANON_PYTHON:-${canon_backend}/venv/bin/python}"
ingest="${canon_backend}/scripts/ingest_unreal_canon.py"
if [[ ! -x "$canon_python" || ! -f "$ingest" ]]; then
  printf '%s\n' 'Nexus ingest script unavailable. Set MEGAJAM_CANON_BACKEND.' >&2
  exit 1
fi
exec "$canon_python" "$ingest" --collection megajam_canon --corpus-dir "${repo}/_config/reference/canon" "$@"
