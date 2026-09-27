"""Independent raw-only scorer for the Issue #3166 gate-truth first rung."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("/evidence")
REPO = Path("/repo")
EXPECTED_SOURCE = {
    "runtime/cli_v1/golden_v3.py": "4325c6e5b662adaa36138dc2f895d31938541a8e030e59b096c60521bb424d5d",
    "runtime/cli_v1/api.py": "a04d1fa2819d9f7199210cc4ac602de020fdf849fa9e3edf0d44568c9a51ddcd",
    "runtime/selector_v1/__init__.py": "66bc2fcb2797b108cd739b1c000352932dbdd7a16c186c1104cd8d26d0645881",
    "runtime/selector_v1/selector.py": "7f3db522b2250fcd3d8960c87b1d87ad078bf1b2b565900b4210836f6b7ca764",
    "runtime/core_v1/__init__.py": "5284bc097858ceeb4793ffc0b88427c8dc693c893e43e1d244aa4be9fcfa7da0",
    "runtime/core_v1/contract.py": "f053f73ccdeb67175068bf4d663bd484d886beb83305ed679510292809afd536",
    "runtime/core_v1/platform_probe.py": "4b373544e163f88cb74f7a739fd2246ae975b26705d609f01280e9480a16582e",
    "runtime/backends/x11_v1/__init__.py": "50a6767fca7c7a81fc1a5e606de60b6660c4e8045ad0b66902d50c4a4493de6b",
    "runtime/backends/x11_v1/backend.py": "3429a422e61ecb8b1f1f278540d0696842d8197d7967803e01bc8d9453bcb4a8",
    "runtime/backends/x11_v1/session.py": "70ffb0167a70efcf629221c8236dd19ba9fbc2ff3ffc18454f13a0f656b86a93",
    "research/integration/golden_v3_second_domain_2246_v1/gtk_fixture_app.py": "a89740107f5b544cde8a0ab1ae9f1af1764498889f85c982d106301577685f4a",
}
raw_path = ROOT / "raw.jsonl"
rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
errors = []
checks = {}


def check(name, condition):
    checks[name] = bool(condition)
    if not condition:
        errors.append(name)


def expected(policy, context):
    dep = context["dependency_current"]
    gate = context["gate"]
    live = gate["truth"] == "TRUE" and gate["fresh"] and gate["intent_match"] and gate["epoch_match"]
    return {
        "TWO_TIER_FRESH_GATE": dep and live,
        "DEPENDENCY_ONLY": dep,
        "GATE_ONLY": live,
        "CACHED_PREPARE_GATE": dep and context["cached_prepare_gate_true"],
    }[policy]


pre = json.loads((ROOT / "preflight.json").read_text(encoding="utf-8"))
check("preflight_pass", pre.get("result") == "PASS_PREFLIGHT" and pre.get("formal_cases_before") == 0)
actual_source = {name: hashlib.sha256((REPO / name).read_bytes()).hexdigest() for name in EXPECTED_SOURCE}
check("source_bytes_independently_pinned", actual_source == EXPECTED_SOURCE and
      pre.get("source_sha256") == EXPECTED_SOURCE)
check("raw_case_count", len(rows) == 25)
check("raw_ids_unique", len({(r.get("case"), r.get("policy")) for r in rows}) == 25)
matrix = [r for r in rows if r["case"] != "valid_gate_no_effect"]
check("24_matrix_rows", len(matrix) == 24)
check("every_policy_has_six_contexts", all(sum(r["policy"] == p for r in matrix) == 6 for p in
      ("TWO_TIER_FRESH_GATE", "DEPENDENCY_ONLY", "GATE_ONLY", "CACHED_PREPARE_GATE")))
check("policy_predictions_match_raw", all(r.get("admitted") is expected(r["policy"], r["context"]) for r in matrix))
valid = [r for r in matrix if r["case"] == "live_true"]
invalid = [r for r in matrix if r["case"] != "live_true"]
check("valid_true_admitted_all", len(valid) == 4 and all(r["admitted"] for r in valid))
check("two_tier_denies_invalid", all(not r["admitted"] for r in invalid if r["policy"] == "TWO_TIER_FRESH_GATE"))
check("gate_only_denies_invalid", all(not r["admitted"] for r in invalid if r["policy"] == "GATE_ONLY"))
check("reduced_policy_unsafe_effects", all(any(r["admitted"] and r["postcondition"] for r in invalid
      if r["policy"] == p) for p in ("DEPENDENCY_ONLY", "CACHED_PREPARE_GATE")))
check("refusal_before_runtime", all(not r["runtime_called"] and r["emissions"] == 0 and r["effect"] is None
      for r in matrix if not r["admitted"]))
check("admitted_useful_rows_have_effect_release", all(r["native_status"] == "completed" and
      r["release_verified"] and r["postcondition"] and r["disposition"] == "EFFECT_VERIFIED_SCOPED"
      for r in matrix if r["admitted"]))
no_effect = [r for r in rows if r["case"] == "valid_gate_no_effect"]
check("no_effect_control_is_hold", len(no_effect) == 1 and no_effect[0]["admitted"] and
      no_effect[0]["native_status"] == "completed" and no_effect[0]["emissions"] > 0 and
      no_effect[0]["effect"] is None and no_effect[0]["disposition"] == "HOLD_POSTCONDITION_UNOBSERVED" and
      any(e.get("type") == "accepted_no_effect" for e in no_effect[0]["events"]))
check("fixture_cleanup_clean", all(r.get("fixture_cleanup", {}).get("error") is None and
      r.get("fixture_cleanup", {}).get("exit_code") == 0 for r in rows))
check("per_case_raw_matches_row_file", all(json.loads((ROOT / "cases" / f"{r['case']}__{r['policy'].lower()}" / "row.json").read_text(encoding="utf-8")) == r for r in rows))

decision = "PASS_GATE_TRUTH_FIRST_RUNG_SCOPED" if not errors else "HOLD_OR_FAIL_GATE_TRUTH_FIRST_RUNG"
report = {"decision": decision, "scope": "Issue #3166 first rung only; full issue remains open",
          "rows": len(rows), "checks": checks, "errors": errors,
          "raw_sha256": hashlib.sha256(raw_path.read_bytes()).hexdigest()}
(ROOT / "AUDIT.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, sort_keys=True))
