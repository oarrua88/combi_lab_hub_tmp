#!/usr/bin/env bash
# CombiLabHUB - build (if needed) and test with 1a30 the Docker image of every SF, one by one.
#   CASF=/path/to/CASF-2016 tools/docker_test_all.sh [sf ...]     (folder names of plugins/)
# Logs go to $LOGDIR/<sf>.log and the summary to $LOGDIR/summary.txt
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGDIR="${LOGDIR:-$REPO/../resultados_docker}"
mkdir -p "$LOGDIR"
LIST=("$@"); [ ${#LIST[@]} -eq 0 ] && LIST=(et_score gb_score onionnet2 sfcnn planet eggnn gign ehign_pla sacnn deattentiondta rfl_score igmodel conbap hacnet delta_linf9_xgb deepbindgcn graphscoredta pointnet pignet2 bapa deeprli mmpd_dta dtitr t_alpha)
echo "Summary $(date)" > "$LOGDIR/summary.txt"
for s in "${LIST[@]}"; do
  echo "===== $s ($(date +%T)) ====="
  if bash "$REPO/plugins/$s/docker_$s.sh" > "$LOGDIR/$s.log" 2>&1 && grep -q "RESULT: PASS" "$LOGDIR/$s.log"; then
    echo "  $s: PASS"; echo "$s  PASS" >> "$LOGDIR/summary.txt"
  else
    echo "  $s: FAIL (see $LOGDIR/$s.log)"; echo "$s  FAIL" >> "$LOGDIR/summary.txt"
  fi
done
cat "$LOGDIR/summary.txt"
