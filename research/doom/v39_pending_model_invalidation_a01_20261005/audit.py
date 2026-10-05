"""Independent post-run audit of retained source, raw and gate outcomes."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
checks = []

def check(name, condition):
    checks.append({"check": name, "passed": bool(condition)})


check("frozen current main identity", freeze.get("main_sha") ==
      "e724d6d795da2852c043cb53cfd92d5a9222a091")
check("construction only", freeze.get("formal_allocation") is False and
      freeze.get("game_model_provider_gui_os_input") is False)
manifest = freeze.get("source_manifest_sha256", {})
manifest_ok = bool(manifest)
for relative, expected in manifest.items():
    path = REPO / Path(relative)
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        manifest_ok = False
check("frozen source/test manifest unchanged", manifest_ok)
latest_main_sha = subprocess.check_output(
    ["git", "rev-parse", "origin/main"], cwd=REPO, text=True).strip()
current_main_closure_ok = True
for relative, expected in manifest.items():
    if relative.startswith("research/doom/v39_pending_model_invalidation_a01_20261005/"):
        continue
    try:
        current = subprocess.check_output(
            ["git", "show", f"origin/main:{relative}"], cwd=REPO)
    except subprocess.CalledProcessError:
        current_main_closure_ok = False
        continue
    if hashlib.sha256(current).hexdigest() != expected:
        current_main_closure_ok = False
check("production import closure unchanged on latest origin/main",
      current_main_closure_ok)

raws = []
for mode in ("normal", "optimized"):
    raw = json.loads((HERE / f"raw-{mode}.json").read_text(encoding="utf-8"))
    raws.append(raw)
    check(f"{mode}: runtime source hash matches freeze",
          raw.get("source_sha256") == manifest.get(
              "research/doom/map01_overlap_controller_v39.py"))
    check(f"{mode}: planner was actively pending",
          raw.get("planner_started_before_invalidation") is True)
    check(f"{mode}: fresh paired health invalidated cover",
          raw.get("fresh_sequence") == 11 and
          raw.get("invalidation_reason") == "health:below_hard_minimum" and
          raw.get("final_admission", {}).get("policy_invalidation", {}).get(
              "outcome", {}).get("requires_new_decision") is True)
    check(f"{mode}: race answer eligible after interruption",
          raw.get("planner_answer_eligible_after_interrupt") is True and
          raw.get("answer_return_ns", 0) >= raw.get("invalidation_evaluated_ns", 1))
    check(f"{mode}: interrupt and matching cancel requested",
          raw.get("planner_interrupt", {}).get("status") == "interrupt_requested" and
          raw.get("cancel_request") == {"op": "cancel", "id": "cover-0"})
    terminal = raw.get("terminal", {})
    release = terminal.get("release", {})
    check(f"{mode}: cancellation terminal carries empty verified receipt",
          terminal.get("id") == "cover-0" and terminal.get("status") == "cancelled" and
          release.get("verified") is True and release.get("keys_down") == [] and
          release.get("buttons_down") == [])
    admission = raw.get("final_admission", {})
    check(f"{mode}: returned answer rejected before executor admission",
          admission.get("status") == "REJECTED_POLICY_INVALIDATED" and
          admission.get("input_authority_admitted") is False and
          admission.get("executor_admission") is None)
    check(f"{mode}: no formal/live allocation",
          raw.get("formal_allocation_invocations") == 0 and
          raw.get("game_model_gui_os_input") is False)

logs_ok = all("Ran 1 test" in (HERE / f"test-{mode}.log").read_text(encoding="utf-8")
              and "OK" in (HERE / f"test-{mode}.log").read_text(encoding="utf-8")
              for mode in ("normal", "optimized"))
check("both local test logs report one passing test", logs_ok)
check("retained normal/optimized source outcomes agree",
      all(raw.get("invalidation_reason") == raws[0].get("invalidation_reason") and
          raw.get("final_admission", {}).get("status") ==
          raws[0].get("final_admission", {}).get("status")
          for raw in raws[1:]))

passed = all(row["passed"] for row in checks)
audit = {
    "schema": "v39-pending-model-invalidation-a01-audit-v1",
    "status": "PASS" if passed else "FAIL",
    "checks_passed": sum(row["passed"] for row in checks),
    "checks_total": len(checks),
    "checks": checks,
    "scope": "independent file/hash/raw consistency audit; not live or physical-release audit",
}
(HERE / "AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n",
                                  encoding="utf-8")

result = {
    "schema": "v39-pending-model-invalidation-a01-result-v1",
    "classification": "PASS_SYNTHETIC_PENDING_MODEL_INVALIDATION_AND_ANSWER_GATE",
    "main_sha": freeze["main_sha"],
    "latest_main_checked_sha": latest_main_sha,
    "source_manifest_files": len(manifest),
    "modes": {mode: "1/1 passed" for mode in ("normal", "optimized")},
    "audit": audit["status"],
    "formal_allocation_invocations": 0,
    "decision": "PASS_FOR_AST_EXTRACTED_CONTROLLER_ORDERING_ONLY",
    "limits": [
        "no real model/provider cancellation or completion race",
        "no live visible threat or Doom/game observation",
        "no GUI, OS input, physical key release, or application effect",
        "no useful-feedback, bounded-recovery, ammo/progress, or terminal outcome evidence",
        "no MAP01 or integrated/product claim",
    ],
}
(HERE / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                                   encoding="utf-8")

if not passed:
    raise SystemExit("independent audit failed")
print(json.dumps({"status": audit["status"],
                  "checks": audit["checks_total"],
                  "result": result["classification"]}, sort_keys=True))
