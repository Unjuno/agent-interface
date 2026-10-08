import json, sys
from pathlib import Path

study=Path(__file__).resolve().parent
run=study.parents[2]/"research/doom/results/map01-astra-attempt-v1"
result=json.loads((study/"RESULT.json").read_text(encoding="utf-8"))
manual=json.loads((run/"failure-analysis-v1.json").read_text(encoding="utf-8"))
assert result["summary"]["cpu_cuda_mismatches"] == 0
assert result["summary"]["matches_retained_manual_decision_labels"] is True
assert result["result"] == "PASS_GPU_CPU_EXACT_PARITY"
assert result["summary"]["invalidated"] == manual["one_way_visual_invalidation"]["health_roi_true_invalidations"]
assert result["summary"]["unchanged"] == manual["one_way_visual_invalidation"]["health_roi_true_unchanged"]
assert all(row["exact_count_match"] and row["status_match"] for row in result["rows"])
print(json.dumps({"audit":"PASS_INDEPENDENT_REPLAY_RECONCILIATION","pairs":len(result["rows"]),"manual_label_counts_match":True,"cpu_gpu_exact_counts_match":True},indent=2))