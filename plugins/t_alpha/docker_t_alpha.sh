#!/usr/bin/env bash
# CombiLabHUB - T-ALPHA with Docker (Linux): builds the image combilab/t_alpha:1.0 (first time only,
# downloads about 2.3 GB from Zenodo) and runs the installation test with CASF-2016 complex 1a30.
#   ./docker_t_alpha.sh        (REBUILD=1 to rebuild the image)
set -u
PLUGIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="combilab/t_alpha:1.0"
echo "============================================================"
echo "  CombiLabHUB - T-ALPHA with Docker (test with complex 1a30)"
echo "============================================================"
if ! docker version >/dev/null 2>&1; then
  echo "ERROR: Docker is not running (or your user cannot use it: sudo usermod -aG docker \$USER)"; exit 1
fi
[ -n "${REBUILD:-}" ] && docker image rm -f "$IMAGE" >/dev/null 2>&1
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Building $IMAGE (first time: about 2.3 GB download and pykeops compilation)..."
  docker build -t "$IMAGE" "$PLUGIN" || { echo "ERROR building the image"; exit 1; }
fi
echo "------------------------------------------------------------"
docker run --rm "$IMAGE" python -W ignore /opt/t_alpha/test_1a30.py --talpha-dir /opt/T-ALPHA --data-dir /opt/talpha_data
rc=$?
echo "------------------------------------------------------------"
exit $rc
