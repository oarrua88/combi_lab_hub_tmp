#!/usr/bin/env bash
# CombiLabHUB - RFL-Score with Docker (Linux): builds the image combilab/rfl_score:1.1 (first time only)
# and runs the installation test with CASF-2016 complex 1a30.
#   CASF=/path/to/CASF-2016 ./docker_rfl_score.sh        (REBUILD=1 to rebuild the image)
set -u
PLUGIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASF="${CASF:-$HOME/CASF-2016/CASF-2016}"
IMAGE="combilab/rfl_score:1.1"
echo "============================================================"
echo "  CombiLabHUB - RFL-Score with Docker (test with complex 1a30)"
echo "============================================================"
if ! docker version >/dev/null 2>&1; then
  echo "ERROR: Docker is not running (or your user cannot use it: sudo usermod -aG docker \$USER)"; exit 1
fi
[ -n "${REBUILD:-}" ] && docker image rm -f "$IMAGE" >/dev/null 2>&1
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Building $IMAGE (first time, several minutes)..."
  docker build -t "$IMAGE" "$PLUGIN" || { echo "ERROR building the image"; exit 1; }
fi
[ -d "$CASF/coreset/1a30" ] || { echo "ERROR: $CASF/coreset/1a30 not found (set CASF)"; exit 1; }
echo "------------------------------------------------------------"
docker run --rm -v "$CASF/coreset/1a30:/complex:ro" "$IMAGE" python -W ignore /opt/rfl_score/test_1a30.py --rfl-dir /opt/rfl-score_v1 --complex /complex --full
rc=$?
echo "------------------------------------------------------------"
exit $rc
