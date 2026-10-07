"""Read-only target/admission linkage audit for the merged A05 archive.

Reads task JSON from the local Git object database at a pinned revision. It does not
run the producer, GUI, provider, container, or study runner.
"""
import collections
import json
import subprocess
from pathlib import Path

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
REF = "58bcbb4c45501880db8782158ddd3add3b765984"
BASE = "research/integration/compiled_comparison_57_4d74_20261004/a05/formal-output"


def read_task(path):
    raw = subprocess.check_output(["git", "-C", REPO, "show", f"{REF}:{BASE}/{path}"])
    return json.loads(raw)


counts = collections.Counter()
rows = []
failures = []
for block in (1, 2):
    for arm in ("A", "B", "C"):
        for task_num in range(1, 7):
            row = read_task(f"block-{block}/{arm}/task-{task_num}.json")
            caller = row["caller"]
            selected = caller.get("selected_target") or {}
            grounding = selected.get("grounding") or {}
            programs = row.get("programs", [])

            if arm == "A":
                program = next(p for p in programs if p["label"] == f"plain-batch-task-{task_num}")
                moves = [a for a in program.get("pointer_admissions", []) if a.get("operation") == "move"]
                for index, key in enumerate(("field_point", "submit_point")):
                    point = grounding.get(key)
                    admission = moves[index] if index < len(moves) else None
                    matched = bool(
                        point and admission and
                        admission.get("payload") == {"x": point[0], "y": point[1]}
                    )
                    counts[(arm, key, "grounding_match" if matched else "mismatch")] += 1
                    rows.append({"block": block, "arm": arm, "task": task_num, "action": key,
                                 "grounding_match": matched})
                    if not matched:
                        failures.append(rows[-1])
                continue

            aliases = selected.get("aliases") or {}
            for kind in ("field", "submit"):
                program_label = (
                    (f"enter-task-{task_num}" if kind == "field" else f"submit-task-{task_num}")
                    if arm == "B" else
                    ("compiled-enter" if kind == "field" else "compiled-submit")
                )
                program = next((p for p in programs if p["label"] == program_label), None)
                if program is None:
                    # A missing C submit program is expected for safe-yield tasks.
                    assert arm == "C" and kind == "submit"
                    continue

                point = grounding.get(f"{kind}_point")
                alias = aliases.get(kind)
                moves = [a for a in program.get("pointer_admissions", []) if a.get("operation") == "move"]
                eligible_checks = [
                    check
                    for candidate in programs
                    for check in candidate.get("target_checks", [])
                    if check.get("handle") == alias
                    and check.get("status") == "VALID"
                    and check.get("eligible") is True
                    and check.get("point") == point
                    and isinstance(check.get("checked_ns"), int)
                    and check["checked_ns"] <= program["started_ns"]
                    and isinstance(check.get("valid_until_ns"), int)
                    and check["valid_until_ns"] >= program["started_ns"]
                ]
                admission = moves[0] if len(moves) == 1 else None
                linked = bool(
                    point and alias and eligible_checks and admission
                    and admission.get("payload") == {"x": point[0], "y": point[1]}
                    and admission.get("admitted_ns", 0) <= eligible_checks[-1]["valid_until_ns"]
                    and admission.get("admitted_ns", 0) <= admission.get("valid_until_ns", -1)
                )
                counts[(arm, kind, "trace_linked" if linked else "unlinked")] += 1
                item = {"block": block, "arm": arm, "task": task_num, "action": kind,
                        "selected_alias": alias, "expected_point": point,
                        "trace_linked": linked,
                        "matching_prior_valid_checks": len(eligible_checks),
                        "move_admissions": len(moves)}
                rows.append(item)
                if not linked:
                    failures.append(item)

assert not failures, failures
assert counts[("A", "field_point", "grounding_match")] == 12
assert counts[("A", "submit_point", "grounding_match")] == 12
assert counts[("B", "field", "trace_linked")] == 12
assert counts[("B", "submit", "trace_linked")] == 12
assert counts[("C", "field", "trace_linked")] == 12
assert counts[("C", "submit", "trace_linked")] == 9

print(json.dumps({
    "ref": REF,
    "source": "merged A05 task JSON records only",
    "counts": {"/".join(k): v for k, v in sorted(counts.items())},
    "executed_BC_actions_trace_linked": sum(v for k, v in counts.items()
        if k[0] in ("B", "C") and k[2] == "trace_linked"),
    "executed_BC_actions_unlinked": sum(v for k, v in counts.items()
        if k[0] in ("B", "C") and k[2] == "unlinked"),
    "failure_count": len(failures),
    "scope_limit": "Trace linkage does not prove all collateral GUI state or the full physical input-authority chain.",
}, indent=2, sort_keys=True))
