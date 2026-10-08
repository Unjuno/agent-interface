import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/input")
OUT = Path("/output")
RAW = ROOT / "RAW.json"
EXPECTED_RAW_SHA = "5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d"
spec = importlib.util.spec_from_file_location("baseline_audit", "/src/baseline_audit.py")
baseline_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline_module)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_path(doc, path, value):
    obj = doc
    for key in path[:-1]:
        obj = obj[key]
    obj[path[-1]] = value


def get_path(doc, path):
    obj = doc
    for key in path:
        obj = obj[key]
    return obj


def same_types(expected, actual):
    if type(expected) is not type(actual):
        return False
    if isinstance(expected, dict):
        return expected.keys() == actual.keys() and all(
            same_types(expected[k], actual[k]) for k in expected
        )
    if isinstance(expected, list):
        return len(expected) == len(actual) and all(
            same_types(a, b) for a, b in zip(expected, actual)
        )
    return True


doc = json.loads(RAW.read_text(encoding="utf-8"))
raw_sha = sha(RAW)
if raw_sha != EXPECTED_RAW_SHA:
    raise SystemExit(f"STOP_RAW_SHA:{raw_sha}")
baseline = baseline_module.audit(doc)
if baseline["status"] != "PASS_DRIFT_BOUNDARY_MAPPED":
    raise SystemExit("HOLD_BASELINE_REJECTED:" + json.dumps(baseline, sort_keys=True))

last = len(doc["distributions"]) - 1
mutations = {
    "cost_A_true": (("cost", "A"), True),
    "drift_grid_zero_false": (("drift_grid", 0), False),
    "final_alpha_true": (("distributions", last, "alpha"), True),
    "state_id_one_true": (("distributions", 0, "rows", 1, "state_id"), True),
    "replay_cost_one_true": (("distributions", 0, "rows", 14, "FROZEN_COST_SELECTIVITY", "cost"), True),
    "semantic_mismatches_zero_false": (("distributions", 0, "summaries", "NAIVE", "semantic_mismatches"), False),
}
mutation_results = {}
for name, (path, replacement) in mutations.items():
    mutant = copy.deepcopy(doc)
    set_path(mutant, path, replacement)
    legacy = baseline_module.audit(mutant)
    legacy_accept = legacy["status"] == "PASS_DRIFT_BOUNDARY_MAPPED"
    strict_reject = not same_types(doc, mutant)
    mutation_results[name] = {
        "legacy_accept": legacy_accept,
        "strict_type_gate_reject": strict_reject,
        "legacy_errors": legacy["errors"],
    }

if not all(v["legacy_accept"] and v["strict_type_gate_reject"] for v in mutation_results.values()):
    raise SystemExit("FAIL_BOOL_BOUNDARY:" + json.dumps(mutation_results, sort_keys=True))

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "baseline_audit.json").write_text(json.dumps(baseline, sort_keys=True, indent=2) + "\n")
(OUT / "mutation_results.json").write_text(json.dumps(mutation_results, sort_keys=True, indent=2) + "\n")
manifest_paths = [
    Path("/src/baseline_audit.py"),
    Path("/src/run_experiment.py"),
    RAW,
    OUT / "baseline_audit.json",
    OUT / "mutation_results.json",
]
manifest = {
    "schema": "issue5006-artifact-hash-manifest-v1",
    "source_sha256": {
        str(p.relative_to("/")): sha(p) for p in manifest_paths[:2]
    },
    "input_sha256": {str(RAW.relative_to("/")): raw_sha},
    "output_sha256": {
        str(p.relative_to("/")): sha(p) for p in manifest_paths[3:]
    },
    "required_paths": [str(p.relative_to("/")) for p in manifest_paths],
}
(OUT / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
verification = subprocess.run(
    [sys.executable, "/src/verify_manifest.py", str(OUT / "manifest.json"), "/"],
    check=False, capture_output=True, text=True,
)
if verification.returncode != 0:
    raise SystemExit("FAIL_MANIFEST_POSITIVE:" + verification.stdout + verification.stderr)

controls = {}
empty = copy.deepcopy(manifest)
empty["source_sha256"] = {}
empty["output_sha256"] = {}
controls["empty_maps_rejected"] = subprocess.run(
    [sys.executable, "/src/verify_manifest.py", "-", "/"],
    input=json.dumps(empty), text=True, capture_output=True,
).returncode != 0
omitted = copy.deepcopy(manifest)
omitted["output_sha256"].pop(omitted["required_paths"][-1])
controls["omitted_path_rejected"] = subprocess.run(
    [sys.executable, "/src/verify_manifest.py", "-", "/"],
    input=json.dumps(omitted), text=True, capture_output=True,
).returncode != 0
changed = copy.deepcopy(manifest)
first_output = changed["output_sha256"]
first_key = next(iter(first_output))
first_output[first_key] = "0" * 64
controls["changed_digest_rejected"] = subprocess.run(
    [sys.executable, "/src/verify_manifest.py", "-", "/"],
    input=json.dumps(changed), text=True, capture_output=True,
).returncode != 0
if not all(controls.values()):
    raise SystemExit("FAIL_MANIFEST_NEGATIVE:" + json.dumps(controls, sort_keys=True))
(OUT / "manifest_controls.json").write_text(json.dumps(controls, sort_keys=True, indent=2) + "\n")
(OUT / "execution.json").write_text(json.dumps({
    "issue": 5006,
    "result": "PASS_AUDIT_BOUNDARY_REPAIRED_SCOPED",
    "raw_sha256": raw_sha,
    "raw_audit": baseline,
    "mutation_count": len(mutation_results),
    "legacy_bool_mutations_accepted": sum(v["legacy_accept"] for v in mutation_results.values()),
    "strict_type_gate_rejected": sum(v["strict_type_gate_reject"] for v in mutation_results.values()),
    "manifest_negative_controls_rejected": sum(controls.values()),
    "execution_architecture": os.uname().machine,
    "execution_python": sys.version,
    "image": "sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9",
    "formal_architecture_match": False,
}, sort_keys=True, indent=2) + "\n")
print("PASS_AUDIT_BOUNDARY_REPAIRED_SCOPED")
print(json.dumps({
    "raw_sha256": raw_sha,
    "baseline_status": baseline["status"],
    "baseline_rows": baseline["row_count"],
    "baseline_distributions": baseline["distribution_count"],
    "bool_mutations_accepted_by_legacy": sum(v["legacy_accept"] for v in mutation_results.values()),
    "bool_mutations_rejected_by_strict_type_gate": sum(v["strict_type_gate_reject"] for v in mutation_results.values()),
    "manifest_negative_controls_rejected": sum(controls.values()),
    "architecture": os.uname().machine,
}, sort_keys=True))
