"""Independent arithmetic and raw-row checks for the terminal-window note."""
import hashlib
import json
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DATA = REPO / "research/doom/results/map01-astra-attempt-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    pins = json.loads((HERE / "TERMINAL_WINDOW_INPUTS.json").read_text())
    mismatches = []
    for rel, expected in pins["inputs"].items():
        if sha(REPO / rel) != expected:
            mismatches.append({"kind": "input-hash", "path": rel})
    report = json.loads((DATA / "report.json").read_text())
    events = [json.loads(row) for row in (DATA / "events.jsonl").read_text().splitlines()]
    manifest = json.loads((DATA / "frame-manifest.json").read_text())
    frame_rows = {row["iteration"]: row for row in manifest}
    rows = {row["sequence"]: row for row in events if row.get("event") == "observation" and row.get("sequence") in {459, 498, 501, 504}}
    if set(rows) != {459, 498, 501, 504}:
        mismatches.append({"kind": "missing-sequences"})
    decision = report["decisions"][11]
    endpoint = report["decisions"][12]
    if PurePosixPath(decision["source_image"]).name != PurePosixPath(rows[459]["image"]).name:
        mismatches.append({"kind": "decision-11-image-link"})
    if PurePosixPath(endpoint["source_image"]).name != PurePosixPath(rows[504]["image"]).name:
        mismatches.append({"kind": "decision-12-image-link"})
    expected_after = [498, 501, 504]
    trace = decision["execution_trace"]
    if [item["receipt"]["after_sequence"] for item in trace] != expected_after:
        mismatches.append({"kind": "receipt-sequences"})
    if any(item["receipt"]["effect_observed_ns"] != rows[n]["capture_ns"] for item, n in zip(trace, expected_after)):
        mismatches.append({"kind": "receipt-clock"})
    for iteration in (11, 12):
        frame_path = DATA / "frames" / f"{iteration:02}.png"
        digest = sha(frame_path)
        if digest != frame_rows[iteration]["sha256"]:
            mismatches.append({"kind": "selected-frame-hash", "iteration": iteration})
    raw = {
        "source_to_terminal_ns": rows[504]["capture_ns"] - rows[459]["capture_ns"],
        "precall_to_start_ns": decision["controller_model_started_ns"] - rows[459]["capture_ns"],
        "controller_span_ns": decision["controller_model_ended_ns"] - decision["controller_model_started_ns"],
        "end_to_terminal_ns": rows[504]["capture_ns"] - decision["controller_model_ended_ns"],
        "action_accept_to_terminal_ns": rows[504]["capture_ns"] - trace[0]["accepted_ns"],
        "model_reported_ns": decision["model_ns"],
    }
    result = json.loads((HERE / "TERMINAL_WINDOW_RESULT.json").read_text())
    expected_ms = {key: value / 1e6 for key, value in (
        ("precall_capture_to_model_start", raw["precall_to_start_ns"]),
        ("controller_model_start_to_end", raw["controller_span_ns"]),
        ("controller_end_to_terminal_capture", raw["end_to_terminal_ns"]),
        ("action_accept_to_terminal_capture", raw["action_accept_to_terminal_ns"]),
        ("precall_capture_to_terminal_capture", raw["source_to_terminal_ns"]),
    )}
    for key, value in expected_ms.items():
        if result["timing_ms"].get(key) != value:
            mismatches.append({"kind": "timing", "field": key})
    if result.get("reported_model_ns") != raw["model_reported_ns"]:
        mismatches.append({"kind": "reported-model-ns"})
    if result.get("selected_frame_sha256") != {str(i): frame_rows[i]["sha256"] for i in (11, 12)}:
        mismatches.append({"kind": "selected-frame-manifest"})
    audit = {
        "schema": "map01-astra-terminal-window-audit-v1",
        "disposition": "PASS_AUDITED_POSTHOC_RECONSTRUCTION" if not mismatches else "FAIL_TERMINAL_WINDOW_AUDIT",
        "sequences_recomputed": sorted(rows),
        "raw_timing_ns_recomputed": raw,
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "scope": "independent timestamp/identity arithmetic only; visual descriptions and health digits remain manual",
    }
    (HERE / "TERMINAL_WINDOW_AUDIT.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps({"disposition": audit["disposition"], "mismatch_count": audit["mismatch_count"], "raw_timing_ns_recomputed": raw}, separators=(",", ":")))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
