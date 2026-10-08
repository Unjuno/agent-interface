"""Run the frozen same-directory/source/summary consumer controls."""
import hashlib
import json
import tempfile
from pathlib import Path

from file_join import classify_run_dir
from test_file_join_bundle import REQUIRED_SOURCES, _json, _jsonl, _sample


ROOT = Path(__file__).resolve().parent
RESEARCH_ROOT = ROOT.parents[1]
FREEZE_PATH = ROOT / "FILE_JOIN_BUNDLE_FREEZE.json"
RAW_PATH = ROOT / "file_join_bundle_raw.json"


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _new_bundle(parent):
    run_dir = parent / "run"
    run_dir.mkdir()
    source_root = parent / "research"
    source_map = {}
    for name in sorted(REQUIRED_SOURCES):
        src = RESEARCH_ROOT / name
        dst = source_root / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        source_map[name] = _sha(dst)
    events = [
        {"event": "command", "received_ns": 99, "emit_ns": 99},
        {"event": "accepted", "id": "recover-1", "accepted_ns": 100,
         "emit_ns": 100},
        {"event": "input_admission", "id": "recover-1", "key": "space",
         "admitted_ns": 120, "input_ack_ns": 121, "emit_ns": 121},
    ]
    samples = [_sample(110, 0), _sample(130, 1)]
    score_events = [{"schema": "independent-progress-event-v2",
                     "event_sequence": 1, "observed_ns": 130,
                     "kind": "KILL_COUNT_INCREASE", "polarity": "positive",
                     "useful": True, "controller_visible": False,
                     "before": {"kill_count": 0},
                     "after": {"kill_count": 1, "delta": 1}}]
    _jsonl(run_dir / "events.jsonl", events)
    _jsonl(run_dir / "scorer-samples.jsonl", samples)
    _jsonl(run_dir / "scorer-events.jsonl", score_events)
    _json(run_dir / "sources.json", source_map)
    _json(run_dir / "scorer-summary.json", {
        "schema": "map01-independent-scorer-integration-v3",
        "controller_visible": False,
        "sample_count": 2,
        "event_count": 1,
        "event_summary": {"events": 1, "positive_useful_events": 1,
                           "negative_events": 0, "first_useful_ns": 130,
                           "kinds": ["KILL_COUNT_INCREASE"]},
        "scheduler": {"missed_sample_periods": 0},
        "sample_interval_ms": {"median": 2e-05, "p95": 2e-05, "max": 2e-05},
        "zero_positive_events_allowed": True,
    })
    return run_dir, source_root, source_map


def _mutate(case_id, run_dir, source_root, source_map):
    if case_id == "valid_bundle":
        return
    if case_id == "missing_sources":
        (run_dir / "sources.json").unlink()
    elif case_id == "missing_required_source":
        del source_map[sorted(REQUIRED_SOURCES)[0]]
        _json(run_dir / "sources.json", source_map)
    elif case_id == "missing_summary":
        (run_dir / "scorer-summary.json").unlink()
    elif case_id == "source_hash_mismatch":
        (source_root / sorted(REQUIRED_SOURCES)[0]).write_text("mutated source\n", encoding="utf-8")
    elif case_id == "source_path_traversal":
        source_map["../../outside.py"] = "0" * 64
        _json(run_dir / "sources.json", source_map)
    elif case_id == "summary_sample_count_mismatch":
        path = run_dir / "scorer-summary.json"
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary["sample_count"] = 99
        _json(path, summary)
    elif case_id == "summary_interval_mismatch":
        path = run_dir / "scorer-summary.json"
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary["sample_interval_ms"]["max"] = 999
        _json(path, summary)
    elif case_id == "summary_event_mismatch":
        path = run_dir / "scorer-summary.json"
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary["event_summary"]["first_useful_ns"] = 110
        _json(path, summary)
    elif case_id == "missing_scorer_events":
        (run_dir / "scorer-events.jsonl").unlink()
    else:
        raise ValueError(f"unhandled frozen case: {case_id}")


def main():
    freeze_bytes = FREEZE_PATH.read_bytes()
    freeze = json.loads(freeze_bytes)
    cases = []
    for case_id, expected in freeze["cases"].items():
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            run_dir, source_root, source_map = _new_bundle(parent)
            if source_map != freeze["required_source_sha256"]:
                raise RuntimeError("current source bytes differ from the frozen source tree")
            _mutate(case_id, run_dir, source_root, source_map)
            observed = classify_run_dir(run_dir, "recover-1", max_gap_ns=100,
                                        research_root=source_root)
            cases.append({"id": case_id, "expected": expected, "observed": observed})
    raw = {
        "schema": "scorer-eventlog-run-bundle-raw-v1",
        "base_main": freeze["base_main"],
        "stack_parent": freeze["stack_parent"],
        "freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "source_sha256": freeze["required_source_sha256"],
        "launch_scope": freeze["launch_scope"],
        "cases": cases,
    }
    RAW_PATH.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(raw, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
