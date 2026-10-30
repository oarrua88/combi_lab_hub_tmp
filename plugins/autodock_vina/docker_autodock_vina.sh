#!/usr/bin/env bash
# CombiLabHUB - AutoDock Vina with Docker (Linux): builds the image combilab/autodock_vina:1.0 (first time only)
# and runs the installation test with CASF-2016 complex 1a30, with both engines (1.1.2 and 1.2.5).
#   CASF=/path/to/CASF-2016 ./docker_autodock_vina.sh        (REBUILD=1 to rebuild the image)
set -u
PLUGIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CASF="${CASF:-$HOME/CASF-2016/CASF-2016}"
IMAGE="combilab/autodock_vina:1.0"
echo "============================================================"
echo "  CombiLabHUB - AutoDock Vina with Docker (test with complex 1a30)"
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
echo "Engine 1.1.2 (MGLTools + Vina 1.1.2, CASF-2016 protocol):"
docker run --rm -v "$CASF/coreset/1a30:/complex:ro" "$IMAGE" python /opt/autodock_vina/test_1a30.py --vina vina --complex /complex
rc1=$?
echo
echo "Engine 1.2.5 (Open Babel + Vina 1.2.5, the Windows engine):"
docker run --rm -v "$CASF/coreset/1a30:/complex:ro" "$IMAGE" python /opt/autodock_vina/test_1a30.py --vina /opt/vina125/vina --complex /complex
rc2=$?
echo "------------------------------------------------------------"
[ $rc1 -eq 0 ] && [ $rc2 -eq 0 ]
