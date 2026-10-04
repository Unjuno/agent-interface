"""Regenerate posthoc v1 bounds/audit from retained v38/v39 raw data; no live rerun."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
RESULTS = PACKAGE / "results"
FROZEN = REPO / "research/doom/results/map01-held-input-occupancy-fulltrace-v4"
SOURCES = [PACKAGE / name for name in
           ("analyze.py", "audit.py", "run_posthoc.py", "test_early_release.py", ".gitattributes")]
SOURCES += sorted((PACKAGE / "dependencies").glob("*.py"))

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    candidate, auditor = load("candidate", PACKAGE / "analyze.py"), load("auditor", PACKAGE / "audit.py")
    audits, invariance, input_hashes = [], {}, {}
    for run_name, label in (("map01-v38-integrated-threat-live-01", "v38"),
                            ("map01-v39-coast-liveness-live-01", "v39")):
        run = REPO / "research/doom/results" / run_name
        report, events = run / "report.json", run / "runtime/events.jsonl"
        output = RESULTS / f"{label}.json"
        value = candidate.analyze(run)
        output.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
        audits.append(auditor.audit(run, output))
        prior = json.loads((FROZEN / output.name).read_text(encoding="utf-8"))
        fields = ("physical_any_key_occupancy_lower_ms", "physical_any_key_occupancy_upper_ms",
                  "occupancy_interval_width_ms", "hold_steps", "no_input_before_admission_steps",
                  "partial_admission_before_keys_held_steps", "cancel_raced_input_ack_steps")
        rows_equal = [(r["id"], r["step"], r["first_key_admitted_ns"], r["first_key_ack_ns"],
                       r["confirmed_any_key_held_until_ns"], r["released_by_ns"],
                       r["physical_any_key_occupancy_lower_ms"], r["physical_any_key_occupancy_upper_ms"])
                      for r in prior["holds"]] == [(r["id"], r["step"], r["first_key_admitted_ns"], r["first_key_ack_ns"],
                       r["confirmed_any_key_held_until_ns"], r["released_by_ns"],
                       r["physical_any_key_occupancy_lower_ms"], r["physical_any_key_occupancy_upper_ms"])
                      for r in value["holds"]]
        decisions_equal = prior["decisions"] == value["decisions"]
        totals_equal = all(prior["totals"].get(field) == value["totals"].get(field) for field in fields)
        if not (rows_equal and decisions_equal and totals_equal):
            raise AssertionError(f"early-release correction changed a trace without qualifying early release: {label}")
        invariance[label] = {"hold_bounds_unchanged": rows_equal, "decision_bounds_unchanged": decisions_equal,
                             "totals_unchanged": totals_equal, "totals": value["totals"]}
        input_hashes[label] = {"report.json": sha(report), "runtime/events.jsonl": sha(events)}
    (RESULTS / "audit.json").write_text(json.dumps({"schema": "map01-held-input-occupancy-early-release-v1-audit",
        "candidate_schema": "early-release-v1", "results": audits, "errors": []}, indent=2) + "\n", encoding="utf-8", newline="\n")
    (RESULTS / "invariance.json").write_text(json.dumps(invariance, indent=2) + "\n", encoding="utf-8", newline="\n")
    manifest = {"schema": "map01-held-input-occupancy-early-release-v2-manifest",
        "source_sha256": {str(p.relative_to(PACKAGE)).replace("\\", "/"): sha(p) for p in SOURCES},
        "raw_sha256": input_hashes,
        "readme_sha256": sha(PACKAGE / "README.md"),
        "output_sha256": {p.name: sha(p) for p in sorted(RESULTS.glob("*.json"))
                          if p.name != "manifest.json"}}
    (RESULTS / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"audits": audits, "invariance": invariance, "manifest": manifest}, indent=2))

if __name__ == "__main__":
    main()
