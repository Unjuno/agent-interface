"""One-shot local Docker runner for Issue #4990."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/src")
OUT = Path("/out")
MODES = ("normal", "opt_flag", "env_opt")
CONTROLS = {
    "stale_success": ('value = ("FAILED_UNKNOWN", False, "NEW_OBSERVATION")',
                      'value = ("SUCCEEDED", False, "NONE")'),
    "authority_success": ('value = ("AUTHORITY_REQUIRED", False, "FOCUS_OR_LEASE")',
                          'value = ("SUCCEEDED", False, "NONE")'),
    "retry_nonblocked": ('elif e["blocked"] is True:\n        value = ("BLOCKED", budget > 0, "UNBLOCK_OR_WAIT")',
                         'elif e["blocked"] is True:\n        value = ("BLOCKED", budget > 0, "UNBLOCK_OR_WAIT")\n    elif e["fresh"] is True:\n        value = ("NO_ACTION", True, "NONE")'),
    "row_count": ('if len(rows)!=384: fail("row_count",len(rows))',
                  'if len(rows)!=385: fail("row_count",len(rows))'),
    "outcome_count": ('if counts!=EXPECTED_COUNTS: fail("outcome_counts",counts)',
                      'if counts!={}: fail("outcome_counts",counts)'),
    "oracle": ('if e["fresh"] is not True: r=("FAILED_UNKNOWN",False,"NEW_OBSERVATION")',
               'if e["fresh"] is not True: r=("SUCCEEDED",False,"NONE")'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(mode, args, env=None):
    if mode == "opt_flag":
        args = [sys.executable, "-O", "-B", *args]
    else:
        args = [sys.executable, "-B", *args]
    child_env = os.environ.copy()
    if mode == "env_opt":
        child_env["PYTHONOPTIMIZE"] = "1"
    else:
        child_env.pop("PYTHONOPTIMIZE", None)
    if env:
        child_env.update(env)
    return subprocess.run(args, cwd=ROOT, env=child_env, capture_output=True)


def save_process(stem, result):
    (OUT / (stem + ".stdout")).write_bytes(result.stdout)
    (OUT / (stem + ".stderr")).write_bytes(result.stderr)
    (OUT / (stem + ".exit")).write_text(str(result.returncode) + "\n", encoding="ascii")


def main():
    if OUT.exists() and any(OUT.iterdir()):
        raise RuntimeError("formal output must be new/empty; no overwrite")
    OUT.mkdir(parents=True, exist_ok=True)
    candidate = ROOT / "candidate.py"
    tests = ROOT / "test_preformal.py"
    source = candidate.read_text(encoding="utf-8")
    for mode in MODES:
        test = invoke(mode, ["-m", "unittest", "-v", "test_preformal"])
        save_process(mode + "-tests", test)
        if test.returncode != 0:
            raise RuntimeError("preformal_tests_failed:" + mode)
        valid = invoke(mode, [str(candidate)])
        save_process(mode, valid)
        if valid.returncode != 0:
            raise RuntimeError("candidate_failed:" + mode)
        receipt = json.loads(valid.stdout)
        if receipt.get("decision") != "PASS_OPTIMIZATION_RESILIENT_CONTRACT_SCOPED":
            raise RuntimeError("candidate_decision_missing:" + mode)
        for name, (before, after) in CONTROLS.items():
            if before not in source:
                raise RuntimeError("mutation_anchor_missing:" + name)
            mutated = source.replace(before, after, 1)
            control_path = OUT / (mode + "-" + name + "-candidate.py")
            control_path.write_text(mutated, encoding="utf-8", newline="\n")
            result = invoke(mode, [str(control_path)])
            stem = mode + "-" + name
            save_process(stem, result)
            control = {
                "passed": result.returncode == 0,
                "pass_marker_seen": b"PASS_OPTIMIZATION_RESILIENT_CONTRACT_SCOPED" in result.stdout,
                "error": result.stderr.decode("utf-8", "replace").strip()[-400:],
                "exit": result.returncode,
                "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
                "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
            }
            (OUT / (stem + ".control")).write_text(
                json.dumps(control, sort_keys=True) + "\n", encoding="utf-8")
            if control["passed"] or control["pass_marker_seen"]:
                raise RuntimeError("corruption_control_not_rejected:" + stem)
        code = ("import runpy; ns=runpy.run_path('/src/candidate.py'); "
                "ns['validate_budget_monotonicity']("
                "{'outcome':'SUCCEEDED','retryable':False},"
                "{'outcome':'BLOCKED','retryable':True},{'probe':'hard-outcome'})")
        budget = invoke(mode, ["-c", code])
        stem = mode + "-budget_monotonicity"
        save_process(stem, budget)
        control = {
            "passed": budget.returncode == 0,
            "pass_marker_seen": b"PASS_OPTIMIZATION_RESILIENT_CONTRACT_SCOPED" in budget.stdout,
            "error": budget.stderr.decode("utf-8", "replace").strip()[-400:],
            "exit": budget.returncode,
            "stdout_sha256": hashlib.sha256(budget.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(budget.stderr).hexdigest(),
        }
        (OUT / (stem + ".control")).write_text(
            json.dumps(control, sort_keys=True) + "\n", encoding="utf-8")
        if control["passed"] or "budget_changed_hard_outcome" not in control["error"]:
            raise RuntimeError("budget_control_not_rejected:" + mode)
    manifest = {p.name: digest(p) for p in sorted(ROOT.iterdir()) if p.is_file()}
    (OUT / "source-manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"formal_status": "COMPLETED", "modes": list(MODES),
                      "controls_per_mode": len(CONTROLS) + 1,
                      "source_manifest": manifest}, sort_keys=True))


if __name__ == "__main__":
    main()
