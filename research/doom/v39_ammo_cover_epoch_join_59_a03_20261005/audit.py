"""Independent audit of raw fixture and retained candidate result; imports no candidate code."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "fixture.json").read_text(encoding="utf-8"))
result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
errors = []
root = HERE.parents[2]
for path, expected in freeze.get("source_files", {}).items():
    blob = subprocess.run(["git", "show", f"{freeze['source_commit']}:{path}"], cwd=root,
                          check=True, stdout=subprocess.PIPE).stdout
    if hashlib.sha256(blob).hexdigest() != expected:
        errors.append(f"frozen source mismatch: {path}")
for field, filename in (("candidate_sha256", "candidate.py"), ("test_sha256", "test_candidate.py"),
                        ("audit_sha256", "audit.py"), ("probe_sha256", "probe.py")):
    if hashlib.sha256((HERE / filename).read_bytes()).hexdigest() != freeze.get(field):
        errors.append(f"frozen construction source mismatch: {filename}")
if hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest() != freeze.get("fixture_sha256"):
    errors.append("frozen fixture mismatch")
expected_names = {"coherent_positive", "minimum_positive_ammo", "zero_ammo",
                  "health_below_floor", "signal_sequence_skew", "signal_capture_skew",
                  "signal_binding_skew"}
if {row["name"] for row in data["cases"]} != expected_names:
    errors.append("fixture case inventory mismatch")
source = data["source_event"]
if source.get("grants_input_authority") is not False or source.get("artifact_published") is not False:
    errors.append("source authority/publication flags unsafe")
source_id = (source.get("sequence"), source.get("capture_ns"), source.get("pointer_binding"))
audited = []
for case in data["cases"]:
    event = case["event"]
    ident = (event.get("sequence"), event.get("capture_ns"), event.get("pointer_binding"))
    identity_ok = True
    signals = event.get("signals", {})
    for name in ("health", "ammo"):
        row = signals.get(name, {})
        if (row.get("sequence"), row.get("capture_ns"), row.get("binding")) != ident:
            identity_ok = False
    valid = identity_ok and event.get("grants_input_authority") is False
    statuses = {}
    if valid:
        for name, floor in (("health", 90), ("ammo", 1)):
            value = signals[name].get("value")
            base = source["signals"][name].get("value")
            statuses[name] = "HARD_INVALIDATED" if value < floor else ("SOFT_CHANGED" if value != base else "UNCHANGED")
    want = "replan" if not valid or any(s == "HARD_INVALIDATED" for s in statuses.values()) else "preserve"
    got = next((r for r in result.get("rows", []) if r.get("name") == case["name"]), None)
    if got is None or got.get("expected") != case["decision"] or got.get("result", {}).get("decision") != want:
        errors.append(f"raw-derived decision mismatch: {case['name']}")
    audited.append({"name": case["name"], "pair_valid": valid, "statuses": statuses, "decision": want})
split = next(r for r in audited if r["name"] == "signal_sequence_skew")
control = result.get("a02_split_epoch_control", {})
if split["decision"] != "replan" or any(v.get("requires_new_decision") for v in control.values()):
    errors.append("A02 counterexample not retained")
if result.get("grants_input_authority") is not False or result.get("all_expected") is not True:
    errors.append("result flags or aggregate mismatch")
report = {"schema": "a03-paired-epoch-audit-v1", "pass": not errors,
          "errors": errors, "raw_derived": audited,
          "fixture_sha256": hashlib.sha256((HERE / "fixture.json").read_bytes()).hexdigest(),
          "result_sha256": hashlib.sha256((HERE / "RESULT.json").read_bytes()).hexdigest()}
print(json.dumps(report, indent=2, sort_keys=True))
sys.exit(0 if not errors else 1)
