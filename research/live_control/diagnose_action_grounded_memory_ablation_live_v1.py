"""Diagnose the frozen audit's missing prereg display field without rewriting it."""
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PLAN = HERE / "action_grounded_memory_ablation_live_v1_prereg.json"
OUT = HERE / "results/action-grounded-memory-ablation-live-01"


def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan, report = read(PLAN), read(OUT / "report.json")
    raw_plans = [read(OUT / "schema-preflight" / "plan.json")]
    raw_plans += [read(OUT / row["name"] / "model" / "plan.json") for row in report["results"]]
    diagnosis = {"schema": "action-grounded-memory-ablation-audit-diagnosis-v1",
        "original_audit_error": "KeyError: requested_model",
        "prereg_requested_model_field_present": "requested_model" in plan,
        "preregistered_runner_sha256": plan["source_sha256"]["visual_memory_model_runner_v1.py"],
        "current_runner_sha256": sha(HERE / "visual_memory_model_runner_v1.py"),
        "raw_call_count": len(raw_plans),
        "raw_requested_models": sorted({row["requested_model"] for row in raw_plans}),
        "raw_requested_efforts": sorted({row["requested_effort"] for row in raw_plans}),
        "formal_output_rewritten": False,
        "interpretation": "machine prereg omitted a redundant model display field; hash-frozen runner and every raw call plan specify Luna-low",
        "scope": "retain original audit failure; use separately versioned retained audit; no rerun"}
    (OUT / "audit-diagnosis.json").write_text(json.dumps(diagnosis, indent=2) + "\n",
                                               encoding="utf-8", newline="\n")
    print(json.dumps(diagnosis, indent=2))


if __name__ == "__main__": main()
