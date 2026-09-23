"""Cross-platform integrity audit for retained matched semantic repair v3."""
import hashlib
import json
import statistics
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = HERE / "results/matched-semantic-repair-live-03"
PLAN = HERE / "matched_semantic_repair_live_v3_prereg.json"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    plan, report = read(PLAN), read(ROOT / "report.json")
    audit, retention = read(ROOT / "audit.json"), read(ROOT / "retention.json")
    arms = report["arms"]
    local = [arm for arm in arms if arm["mode"] == "local"]
    model = [arm for arm in arms if arm["mode"] == "model"]
    token_advantage = statistics.median(arm["usage"]["input_tokens"] for arm in model) - \
        statistics.median(arm["usage"]["input_tokens"] for arm in local)
    recovery_advantage = statistics.median(
        arm["metrics_ms"]["recovery_from_resized_capture_ms"] for arm in model) - \
        statistics.median(arm["metrics_ms"]["recovery_from_resized_capture_ms"] for arm in local)
    call_ids = [record["call_id"] for arm in arms for record in arm["model_records"]]
    checks = {
        "manifest": all((ROOT / name).is_file() and sha(ROOT / name) == digest
                        for name, digest in retention["manifest"].items()),
        "frozen_sources": all((REPO / name).is_file() and sha(REPO / name) == digest
                              for name, digest in plan["source_sha256"].items()),
        "retained_pass": retention["decision"] == "RETAIN_PASSED_FIRST_OUTCOME_NO_RETRY"
            and report["passed"] is True and audit["passed"] is True,
        "all_arms": len(arms) == 4 and all(arm["passed"] is True for arm in arms),
        "correct_release": all(arm["actual"] == {"value": ["t000215"]}
            and arm["checks"]["released"] and arm["checks"]["reconciled"] for arm in arms),
        "post_model_current": all(arm["post_model_revalidation"]
            ["status"] == "CURRENT_PATCH_MATCH_NO_AUTHORITY"
            and arm["post_model_revalidation"]["current_sequence"] >
                arm["post_model_revalidation"]["model_source_sequence"]
            and arm["post_model_revalidation"]["grants_input_authority"] is False
            for arm in model),
        "call_accounting": len(call_ids) == len(set(call_ids)) == 6
            and [arm["metrics_ms"]["model_calls"] for arm in arms] == [1, 2, 2, 1],
        "metrics": token_advantage == report["metrics"]["input_token_advantage"]
            and recovery_advantage == report["metrics"]["recovery_ms_advantage"],
        "gates": token_advantage >= plan["thresholds"]["minimum_input_token_advantage"]
            and recovery_advantage >= plan["thresholds"]["minimum_recovery_ms_advantage"],
        "zero_retry": all(arm["retry_count"] == 0 for arm in arms),
    }
    result = {"passed": all(checks.values()), "checks": checks,
        "input_token_advantage": token_advantage,
        "recovery_ms_advantage": recovery_advantage,
        "model_calls": len(call_ids), "files_in_manifest": len(retention["manifest"]),
        "bytes_before_receipt": retention["bytes"], "scope": report["scope"]}
    (ROOT / "retained-audit.json").write_text(json.dumps(result, indent=2)+"\n",
        encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
