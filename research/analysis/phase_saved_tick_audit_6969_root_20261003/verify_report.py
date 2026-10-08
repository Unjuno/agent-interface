"""Read-only saved-report coverage check; imports no reconstruction code."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent / "exogenous_phase_6803_derived_capture_a05_20261003_3cbf"
result = json.loads((HERE / "RESULT.json").read_bytes())
raw = json.loads((STUDY / "formal_02/candidate/raw.json").read_bytes())
receipt = json.loads((HERE / "AUDIT.json").read_bytes())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


paths = {}
stack = [((), raw)]
while stack:
    path, value = stack.pop()
    if type(value) is dict:
        stack.extend((path + (key,), child) for key, child in value.items())
    elif type(value) is list:
        stack.extend((path + (index,), child) for index, child in enumerate(value))
    else:
        paths[path] = value
seen = set()
for control in result["scalar_controls"]:
    path = tuple(control["path"])
    require(path in paths and path not in seen, "unknown/duplicate control path")
    seen.add(path)
    require(canonical(paths[path]) == canonical(control["original"]), "original mismatch")
    require(canonical(control["replacement"]) != canonical(control["original"]), "no-op control")
    require(control["effective"] is True and control["rejected"] is True, "control failed")
require(seen == set(paths), "missing scalar coverage")
aliases = {path for path, value in paths.items() if type(value) is int and value in (0, 1)}
require({tuple(c["path"]) for c in result["type_alias_controls"]} == aliases, "alias coverage")
for control in result["type_alias_controls"]:
    value = paths[tuple(control["path"])]
    require(value == bool(value) and canonical(value) != canonical(bool(value)), "alias ineffective")
    require(all(control[key] is True for key in ("effective", "rejected", "python_equality_alias")),
            "alias report failed")
require(len(result["structural_controls"]) == 4, "structural count")
require(all(c["effective"] is True and c["rejected"] is True
            for c in result["structural_controls"]), "structural control failed")
require(result["total_controls"] == len(seen) + len(aliases) + 4 == result["effective_rejected"],
        "control totals")
require(result["baseline_exact_match"] is True and result["rows"] == len(raw["rows"]) == 147,
        "baseline report")
require(result["boundary_counts"] == dict(Counter(row["boundary"] for row in raw["rows"])),
        "boundary counts")
require((HERE / "exit.txt").read_text().strip() == "0" and (HERE / "stderr.txt").read_bytes() == b"",
        "execution receipt")
require(receipt["result_sha256"] == hashlib.sha256((HERE / "RESULT.json").read_bytes()).hexdigest(),
        "result hash")
require(receipt["original_raw_sha256"] == hashlib.sha256(
    (STUDY / "formal_02/candidate/raw.json").read_bytes()).hexdigest(), "raw hash")
print("PASS_SAVED_REPORT_COVERAGE scalar=2058 aliases=8 structural=4")
