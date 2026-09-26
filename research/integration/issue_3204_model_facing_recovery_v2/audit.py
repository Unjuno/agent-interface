"""Independent result audit; intentionally does not import experiment code."""
import hashlib
import json
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    root = Path("/audit")
    result = json.loads((root / "RESULT.json").read_text())
    manifest = json.loads((root / "manifest.json").read_text())
    freeze = json.loads((root / "FREEZE.json").read_text())
    bridge = json.loads((root / "BRIDGE_SUMMARY.json").read_text())
    checks = {}
    checks["formal_mode"] = result.get("run_mode") == "FORMAL"
    checks["allocation"] = result.get("allocation") == manifest["allocation"]
    checks["scenario_policy_grid"] = len(result.get("rows", [])) == 12
    checks["action_free"] = result.get("action_calls") == 0 and result.get("effect_claims") == 0
    checks["bridge_identity"] = bridge.get("mode") == "LOCAL_OLLAMA" and bridge.get("digest") == freeze["model_digest"]
    checks["bridge_call_count"] = bridge.get("calls") == 9 and result.get("model_calls") == 9
    rpc = root / "rpc"
    receipts = {str(item["call_id"]): item for item in bridge.get("receipts", [])}
    checks["rpc_receipt_count"] = len(receipts) == 9
    checks["frozen_sources"] = all(
        digest((root / name).read_bytes()) == expected
        for name, expected in freeze["sha256"].items()
    )
    checks["frozen_result"] = result.get("freeze_sha256") == digest((root / "FREEZE.json").read_bytes())
    keyed = {(row["scenario"], row["policy"]): row for row in result.get("rows", [])}
    expected_answers = {item["id"]: item["expected"] for item in manifest["scenarios"]}
    checks["unique_grid"] = len(keyed) == 12
    image_check = True
    call_check = True
    model_check = True
    for scenario in manifest["scenarios"]:
        image_path = root / "output" / "images" / f"{scenario['id']}.png"
        image_hash = digest(image_path.read_bytes())
        for policy in manifest["policies"]:
            row = keyed.get((scenario["id"], policy))
            if row is None:
                image_check = call_check = model_check = False
                continue
            image_check &= row.get("image_sha256") == image_hash
            image_check &= row.get("expected") == expected_answers[scenario["id"]]
            if row.get("model_called"):
                response = row.get("response", {})
                call_id = row.get("call_id")
                request_path = rpc / f"request-{call_id}.json"
                response_path = rpc / f"response-{call_id}.json"
                request_bytes = request_path.read_bytes() if request_path.exists() else b""
                response_bytes = response_path.read_bytes() if response_path.exists() else b""
                receipt = receipts.get(call_id, {})
                call_check &= bool(request_bytes and response_bytes)
                call_check &= receipt.get("request_sha256") == digest(request_bytes)
                call_check &= receipt.get("response_sha256") == digest(response_bytes)
                call_check &= json.loads(response_bytes) == response if response_bytes else False
                request_obj = json.loads(request_bytes) if request_bytes else {}
                call_check &= digest(json.dumps(request_obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()) == row.get("request_sha256")
                call_check &= request_obj.get("image_sha256") == row.get("image_sha256")
                call_check &= request_obj.get("model_digest") == freeze["model_digest"]
                call_check &= response.get("status") == "OK"
                call_check &= row.get("request_sha256") is not None
                model_check &= response.get("model_digest") == freeze["model_digest"]
                body = response.get("ollama_response", {})
                model_check &= body.get("model", "").split(":")[0] == freeze["model"].split(":")[0]
                model_check &= row.get("answer") in {"READY", "BLOCKED", "ABSTAIN"}
            else:
                call_check &= row.get("scenario") == "cross_epoch_conflict" and policy in {
                    "TYPED_EPOCH_AWARE_COMPOSER", "EPOCH_REJECT_ONLY"
                }
                call_check &= row.get("answer") == "ABSTAIN"
    checks["images_bound"] = bool(image_check)
    checks["rpc_responses"] = bool(call_check)
    checks["model_identity_per_call"] = bool(model_check)
    candidate = [keyed.get((s, "TYPED_EPOCH_AWARE_COMPOSER"), {}) for s in expected_answers]
    rejector = [keyed.get((s, "EPOCH_REJECT_ONLY"), {}) for s in expected_answers]
    checks["candidate_exact_oracle"] = all(row.get("answer") == expected_answers[s] for s, row in zip(expected_answers, candidate))
    checks["candidate_conflict_preabstain"] = (
        keyed.get(("cross_epoch_conflict", "TYPED_EPOCH_AWARE_COMPOSER"), {}).get("model_called") is False
    )
    checks["candidate_useful_coverage"] = sum(row.get("answer") == expected_answers[s] for s, row in zip(expected_answers, candidate)) > sum(row.get("answer") == expected_answers[s] for s, row in zip(expected_answers, rejector))
    altered_answer = dict(keyed.get(("aligned", "TYPED_EPOCH_AWARE_COMPOSER"), {}), answer="CORRUPTED")
    altered_conflict = dict(keyed.get(("cross_epoch_conflict", "TYPED_EPOCH_AWARE_COMPOSER"), {}), model_called=True)
    checks["corruption_controls"] = (
        altered_answer.get("answer") != expected_answers["aligned"]
        and altered_conflict.get("model_called") is not False
        and not all(keyed.get((s, "TYPED_EPOCH_AWARE_COMPOSER"), {}).get("answer") == expected_answers[s] for s in expected_answers if s != "aligned")
    )
    infrastructure_keys = ("formal_mode", "allocation", "scenario_policy_grid", "action_free",
                           "bridge_identity", "bridge_call_count", "rpc_receipt_count", "frozen_sources",
                           "frozen_result", "unique_grid", "images_bound", "rpc_responses",
                           "model_identity_per_call", "corruption_controls")
    integrity_ok = all(checks[key] for key in infrastructure_keys)
    candidate_exact = checks["candidate_exact_oracle"]
    candidate_safe = checks["candidate_conflict_preabstain"]
    useful = checks["candidate_useful_coverage"]
    if not integrity_ok:
        gate = "STOP_EVIDENCE_OR_PROVENANCE_INVALID"
    elif not candidate_safe or not candidate_exact:
        gate = "FAIL_MODEL_FACING_EPOCH_COMPOSITION_SCOPED"
    elif not useful:
        gate = "HOLD_NO_USEFUL_COVERAGE_GAIN"
    else:
        gate = "PASS_MODEL_FACING_EPOCH_COMPOSITION_SCOPED"
    output = {"audit_version": "independent-v1", "gate": gate, "checks": checks,
              "candidate_answers": [row.get("answer") for row in candidate],
              "reject_only_answers": [row.get("answer") for row in rejector]}
    (root / "AUDIT.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))
    raise SystemExit(0 if gate.startswith("PASS_") else 2)


if __name__ == "__main__":
    main()
