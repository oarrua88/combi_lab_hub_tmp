#!/usr/bin/env bash
# CombiLabHUB - GraphscoreDTA with Docker (Linux): builds the image combilab/graphscoredta:1.0 (first time only)
# and runs the installation test with CASF-2016 complex 1a30.
#   CASF=/path/to/CASF-2016 ./docker_graphscoredta.sh        (REBUILD=1 to rebuild the image)
set -u
PLUGIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASF="${CASF:-$HOME/CASF-2016/CASF-2016}"
IMAGE="combilab/graphscoredta:1.0"
echo "============================================================"
echo "  CombiLabHUB - GraphscoreDTA with Docker (test with complex 1a30)"
echo "============================================================"
if ! docker version >/dev/null 2>&1; then
  echo "ERROR: Docker is not running (or your user cannot use it: sudo usermod -aG docker \$USER)"; exit 1
fi
[ -n "${REBUILD:-}" ] && docker image rm -f "$IMAGE" >/dev/null 2>&1
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Building $IMAGE (first time, several minutes)..."
  docker build -t "$IMAGE" "$PLUGIN" || { echo "ERROR building the image"; exit 1; }
fi
echo "------------------------------------------------------------"
docker run --rm "$IMAGE"
rc=$?
echo "------------------------------------------------------------"
exit $rc
