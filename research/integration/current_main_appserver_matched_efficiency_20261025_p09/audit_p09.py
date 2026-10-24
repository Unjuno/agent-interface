"""Independent offline audit and paired summaries for P09 first outcomes."""
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ARMS = ("direct_public_input", "compiled_public_caller")
PAIRS = ("p01", "p02", "p03")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def audit():
    trials = {}
    checks = {}
    for pair in PAIRS:
        for arm in ARMS:
            key = f"{pair}-{arm}"
            run = ROOT / "run" / key
            result_path = run / "RESULT.json"
            if not result_path.is_file():
                raise FileNotFoundError(f"missing retained first outcome: {key}")
            result = json.loads(result_path.read_text(encoding="utf-8"))
            ledger = json.loads((run / "LEDGER-RECONCILED.json").read_text(encoding="utf-8"))
            selected = json.loads((run / "model-selected-point.json").read_text(encoding="utf-8"))
            redactions = json.loads((run / "REDACTIONS.json").read_text(encoding="utf-8"))
            clicks = list((run / "server").rglob("synthetic-target-click.json"))
            effects = list((run / "server").rglob("synthetic-effect-receipt.json"))
            manifest = []
            for line in (run / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
                digest, rel = line.split("  ", 1)
                actual = sha((run / Path(rel)).read_bytes())
                manifest.append(actual == digest)
            trial_checks = {
                "identity": result.get("pair") == pair and result.get("arm") == arm,
                "single_provider_turn": result.get("provider_status") == "completed" and
                    result.get("provider_usage", {}).get("status") == "reported",
                "correct_route_returned": result.get("action_status") == "returned",
                "model_used_public_observation": result.get("model_image_sha256") == result.get("observation_image_sha256"),
                "mint_bound_to_observation": result.get("mint_source_sequence") == result.get("observation_sequence") == result.get("mint_created_sequence"),
                "independent_task_success": result.get("independent_task_success") is True,
                "release_verified": result.get("release_verified") is True,
                "one_click_and_effect": result.get("owner_button_press_count") == 1 and len(clicks) == 1 and len(effects) == 1,
                "runtime_score_not_trusted": result.get("runtime_task_success") is None,
                "ledger_complete": ledger.get("complete") is True,
                "selected_point_retained": selected.get("point") == result.get("selected_point"),
                "privacy_hashes_match": all(row.get("redacted_sha256") == sha((run / row["path"]).read_bytes()) for row in redactions.get("redactions", [])),
                "raw_manifest_matches": bool(manifest) and all(manifest),
                "no_wslc_or_physical_input": result.get("wslc_used") is False and result.get("physical_input") is False,
            }
            checks[key] = trial_checks
            trials[key] = result
    paired = {}
    for pair in PAIRS:
        left, right = (trials[f"{pair}-{arm}"] for arm in ARMS)
        paired[pair] = {}
        for metric in ("provider_turn_ms", "observation_to_action_return_ms", "total_trial_ms", "input_tokens", "output_tokens", "reasoning_output_tokens"):
            a, b = left.get(metric), right.get(metric)
            if type(a) in (int, float) and type(b) in (int, float):
                paired[pair][metric + "_direct_minus_compiled"] = a - b
    per_arm = {}
    for arm in ARMS:
        subset = [trials[f"{pair}-{arm}"] for pair in PAIRS]
        per_arm[arm] = {
            "n": len(subset), "independent_successes": sum(t.get("independent_task_success") is True for t in subset),
            "verified_releases": sum(t.get("release_verified") is True for t in subset),
            "provider_turn_ms": [t.get("provider_turn_ms") for t in subset],
            "observation_to_action_return_ms": [t.get("observation_to_action_return_ms") for t in subset],
            "total_trial_ms": [t.get("total_trial_ms") for t in subset],
            "input_tokens": [t.get("input_tokens") for t in subset],
            "output_tokens": [t.get("output_tokens") for t in subset],
            "reasoning_output_tokens": [t.get("reasoning_output_tokens") for t in subset],
        }
    report = {"schema":"agent-interface/appserver-matched-efficiency-p09-audit-v1",
      "classification":"PASS_SCOPED" if all(all(c.values()) for c in checks.values()) else "FAIL_OR_HOLD",
      "checks":checks,"per_arm":per_arm,"paired_differences":paired,
      "paired_medians":{k:statistics.median(v for row in paired.values() if (v:=row.get(k)) is not None) for k in sorted({m for row in paired.values() for m in row})},
      "scope":"three matched Fake X pairs; descriptive evidence only; no live GUI or WSLc claim",
      "physical_input":False,"wslc_used":False}
    (ROOT / "AUDIT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    return report

if __name__ == "__main__":
    report=audit(); print(json.dumps(report,indent=2,sort_keys=True))
    raise SystemExit(0 if report["classification"]=="PASS_SCOPED" else 1)
