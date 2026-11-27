"""Independent integrity and decision-rule audit for p06 retained results."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUN = ROOT / "run"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit():
    result_path = RUN / "RESULT.json"
    if not result_path.is_file():
        raise FileNotFoundError("p06 terminal result is missing")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    ledger = json.loads((RUN / "LEDGER-RECONCILED.json").read_text(encoding="utf-8"))
    selected = json.loads((RUN / "model-selected-point.json").read_text(encoding="utf-8"))
    prelaunch = json.loads((ROOT / "PRELAUNCH.json").read_text(encoding="utf-8"))
    redactions = json.loads((ROOT / "REDACTIONS.json").read_text(encoding="utf-8"))
    click_files = list((RUN / "server").glob("*/synthetic-target-click.json"))
    effect_files = list((RUN / "server").glob("*/synthetic-effect-receipt.json"))
    checks = {
        "result_pass_classification": result.get("classification") ==
            "PASS_MODEL_GROUNDED_PUBLIC_MCP_FAKE_X_ONLY",
        "one_completed_real_model_turn": result.get("provider_status") == "completed",
        "reported_model_usage": isinstance(result.get("provider_usage"), dict) and
            result["provider_usage"].get("status") == "reported",
        "caller_submitted_model_derived_mint": result.get("tool_call_submitted") is True,
        "public_mint_succeeded": result.get("mint_status") == "minted",
        "mint_bound_to_observed_sequence": result.get("mint_source_sequence") ==
            result.get("observation_sequence"),
        "mint_receipt_created_on_observed_sequence": result.get("mint_created_sequence") ==
            result.get("observation_sequence"),
        "model_used_exact_public_observation_image": result.get("model_image_sha256") ==
            result.get("observation_image_sha256"),
        "public_compiled_call_returned": result.get("compiled_status") == "returned",
        "model_point_matches_terminal": selected.get("point") == result.get("selected_point"),
        "model_point_inside_target": result.get("selected_point_inside_green") is True,
        "owner_click_inside_target": result.get("owner_click_inside_green") is True,
        "owner_click_matches_model_point": result.get("owner_click_matches_model_point") is True,
        "exactly_one_click_effect": result.get("owner_button_press_count") == 1,
        "one_owner_click_receipt": len(click_files) == 1,
        "one_independent_effect_receipt": len(effect_files) == 1,
        "independent_task_score": result.get("independent_task_success") is True,
        "runtime_task_score_remains_null": result.get("runtime_task_success") is None,
        "all_attempt_ledger_complete": ledger.get("complete") is True,
        "prelaunch_freeze_present": prelaunch.get("classification") == "FROZEN_BEFORE_PROVIDER_CALL",
        "redaction_hashes_match": all(
            row.get("redacted_sha256") == sha((ROOT / row["path"]).read_bytes())
            for row in redactions.get("redactions", [])),
        "no_wslc_or_physical_input": result.get("wslc_used") is False and
            result.get("physical_input") is False,
    }
    manifest_path = RUN / "SHA256SUMS"
    manifest_rows = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        path = RUN / Path(rel)
        manifest_rows.append({"path": rel, "expected": digest,
                              "actual": sha(path.read_bytes()),
                              "match": sha(path.read_bytes()) == digest})
    checks["manifest_all_match"] = bool(manifest_rows) and all(
        row["match"] for row in manifest_rows)
    report = {
        "schema": "agent-interface/appserver-visual-grounding-p06-audit-v1",
        "classification": "PASS_SCOPED" if all(checks.values()) else "FAIL_OR_HOLD",
        "checks": checks,
        "manifest_count": len(manifest_rows),
        "manifest": manifest_rows,
        "scope": "real model selection through standard caller on synthetic Fake X only",
        "physical_input": False,
        "wslc_used": False,
    }
    (ROOT / "AUDIT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8", newline="\n")
    return report


if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["classification"] == "PASS_SCOPED" else 1)
