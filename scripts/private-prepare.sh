#!/usr/bin/env bash
# Reconstruct the source in a child directory; never replace checkout metadata.
set -euo pipefail
BASE=$(grep -Ev '^\s*(#|$)' upstream-base.txt | head -n1 | tr -d '[:space:]')
CACHE="${RUNNER_TEMP:?}/node-upstream-${BASE}"
if [ ! -d "$CACHE/.git" ]; then scripts/clone-upstream.sh https://github.com/nodejs/node.git "$BASE" "$CACHE"; fi
[ "$(git -C "$CACHE" rev-parse HEAD)" = "$BASE" ] || { echo 'Upstream cache mismatch'; exit 1; }
UPSTREAM_REPO="file://$CACHE" scripts/prepare.sh source
