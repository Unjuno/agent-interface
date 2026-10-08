"""Zero-target-invocation construction gate for the terminality probe."""
import json
import os
import platform
import sys
from pathlib import Path

from freeze_provenance import verify_frozen_sources


ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
T3 = ROOT / "research/live_control/owner_keyup_keymap_witness_5156_t3_v1"


def main():
    freeze = json.loads((PACKAGE / "FREEZE.json").read_text(encoding="utf-8"))
    problems = []
    if platform.python_version() != "3.14.5":
        problems.append("Python version mismatch")
    source_check, source_problems = verify_frozen_sources(ROOT, freeze)
    problems.extend(source_problems)

    sys.path.insert(0, str(T3))
    old_cwd = Path.cwd()
    try:
        os.chdir(T3)
        import test_audit_formal_x11 as fixture_module
    finally:
        os.chdir(old_cwd)
    rows = fixture_module.fixture_rows()
    completions = [row for row in rows if row.get("event") == "runner_complete"]
    if len(completions) != 1:
        problems.append(f"fixture completion count is {len(completions)}")
        control = []
        treatment = []
    else:
        body = [row for row in rows if row is not completions[0]]
        marker = dict(completions[0])
        marker["raw_rows"] = len(body) + 1
        control = body + [marker]
        treatment = [marker] + body
        if control[-1] is not marker or treatment[0] is not marker:
            problems.append("marker placement construction failed")
        if control[:-1] != treatment[1:]:
            problems.append("non-completion records differ")
        if marker.get("exit_code") != 0 or type(marker.get("exit_code")) is not int:
            problems.append("completion control is not integer zero")
        if marker.get("raw_rows") != len(control):
            problems.append("completion raw_rows count is inconsistent")

    OUT = PACKAGE / "results/formal-01"
    OUT.mkdir(parents=True, exist_ok=True)
    status = "STOP_INVALID_CONTROL_OR_PROVENANCE" if problems else "PASS_SOURCE_FIXTURE_CONSTRUCTION"
    result = {
        "status": status,
        "source_commit": freeze["main_commit"],
        "source_check": source_check,
        "python_version": sys.version,
        "positive_control_rows": len(control),
        "treatment_rows": len(treatment),
        "completion_count": len(completions),
        "control_completion_last": bool(control and control[-1].get("event") == "runner_complete"),
        "treatment_completion_first": bool(treatment and treatment[0].get("event") == "runner_complete"),
        "noncompletion_sequences_equal": bool(control and control[:-1] == treatment[1:]),
        "candidate_cli_invocations": 0,
        "problems": problems,
    }
    (OUT / "PREFLIGHT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                          encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
