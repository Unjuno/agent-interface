"""Read MAP01 v15 JSONL artifacts and classify one intent's scorer interval."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
from pathlib import PurePosixPath
from pathlib import Path

from candidate import classify_intent


REQUIRED_SOURCES = {
    "doom/session_map01_v12.py",
    "doom/session_map01_v13.py",
    "doom/map01_scorer_stdio_adapter_v1.py",
    "doom/main_thread_scorer_polling_v1.py",
    "doom/independent_progress_clock_v2.py",
    "doom/doom_retained_input_backend_v3.py",
    "live_control/input_transition_owner_v3.py",
}
SAMPLE_FIELDS = {
    "schema", "sample_ns", "kill_count", "death_count", "episode_finished",
    "player_dead", "map_exit",
}
EVENT_SCHEMA = "independent-progress-event-v2"
SAMPLE_SCHEMA = "independent-progress-sample-v2"
SUMMARY_SCHEMA = "map01-independent-scorer-integration-v3"
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


def _read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f"blank JSONL row at {line_number}")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"JSONL row {line_number} is not an object")
            rows.append(row)
    return rows


def classify_files(events_path, scorer_samples_path, intent_id, *, max_gap_ns):
    """Legacy two-path helper for the original synthetic construction fixtures.

    New consumers must call :func:`classify_run_dir`; this helper intentionally
    has no run-sidecar or source-provenance guarantee.
    """
    try:
        events = _read_jsonl(events_path)
        samples = _read_jsonl(scorer_samples_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        return {"decision": "POST_CANCELLATION_COOCCURRENCE",
                "reason": "invalid_or_missing_runtime_jsonl",
                "error_type": type(exc).__name__, "causal_attribution": False}
    return classify_intent(events, samples, intent_id, max_gap_ns=max_gap_ns)


def _bundle_file(root, name):
    path = root / name
    resolved = path.resolve(strict=True)
    if resolved.parent != root.resolve() or not resolved.is_file():
        raise ValueError(f"run artifact is not a regular file in run directory: {name}")
    return resolved


def _read_json(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON sidecar is not an object: {path.name}")
    return value


def _validate_sources(sources, research_root):
    if not isinstance(sources, dict) or not REQUIRED_SOURCES.issubset(sources):
        raise ValueError("sources.json lacks the required runtime dependency closure")
    root = Path(research_root).resolve(strict=True)
    for name, digest in sources.items():
        if not isinstance(name, str) or "\\" in name:
            raise ValueError("sources.json contains a noncanonical source path")
        relative = PurePosixPath(name)
        local = Path(*relative.parts)
        if (relative.is_absolute() or local.is_absolute() or local.drive
                or relative.as_posix() != name
                or any(part in ("", ".", "..") for part in relative.parts)):
            raise ValueError("sources.json contains an unsafe source path")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise ValueError(f"sources.json contains an invalid SHA-256: {name}")
        path = (root / Path(*relative.parts)).resolve(strict=True)
        if root not in path.parents or not path.is_file():
            raise ValueError(f"source path escapes research root or is not a file: {name}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError(f"source hash mismatch: {name}")


def _event_summary(events):
    positive = [row for row in events if row.get("useful") is True]
    negative = [row for row in events if row.get("polarity") == "negative"]
    return {
        "events": len(events),
        "positive_useful_events": len(positive),
        "negative_events": len(negative),
        "first_useful_ns": min((row["observed_ns"] for row in positive), default=None),
        "kinds": [row.get("kind") for row in events],
    }


def _same_json_value(actual, expected):
    """Compare JSON values without Python's bool/int equality coercion."""
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return (actual.keys() == expected.keys()
                and all(_same_json_value(actual[key], value)
                        for key, value in expected.items()))
    if isinstance(expected, list):
        return (len(actual) == len(expected)
                and all(_same_json_value(a, b) for a, b in zip(actual, expected)))
    return actual == expected


def _expected_scorer_events(samples):
    """Independently reconstruct event rows from adjacent scorer samples."""
    expected = []
    previous = None

    def add(observed_ns, kind, polarity, useful, before, after):
        expected.append({
            "schema": EVENT_SCHEMA,
            "event_sequence": len(expected) + 1,
            "observed_ns": observed_ns,
            "kind": kind,
            "polarity": polarity,
            "useful": useful,
            "controller_visible": False,
            "before": before,
            "after": after,
        })

    for sample in samples:
        current = sample["payload"]
        if current["map_exit"] and (not current["episode_finished"] or current["player_dead"]):
            raise ValueError("scorer sample map-exit state is invalid")
        if previous is None:
            previous = current
            continue

        if previous["episode_finished"]:
            state_keys = ("kill_count", "death_count", "episode_finished",
                          "player_dead", "map_exit")
            if any(current[key] != previous[key] for key in state_keys):
                raise ValueError("terminal scorer state mutated within one run bundle")
            previous = current
            continue
        if (current["kill_count"] < previous["kill_count"]
                or current["death_count"] < previous["death_count"]
                or (previous["map_exit"] and not current["map_exit"])):
            raise ValueError("scorer counter or map-exit state regressed")

        observed_ns = current["sample_ns"]
        if current["kill_count"] > previous["kill_count"]:
            add(observed_ns, "KILL_COUNT_INCREASE", "positive", True,
                {"kill_count": previous["kill_count"]},
                {"kill_count": current["kill_count"],
                 "delta": current["kill_count"] - previous["kill_count"]})
        if current["death_count"] > previous["death_count"]:
            add(observed_ns, "DEATH_COUNT_INCREASE", "negative", False,
                {"death_count": previous["death_count"]},
                {"death_count": current["death_count"],
                 "delta": current["death_count"] - previous["death_count"]})
        if current["player_dead"] and not previous["player_dead"]:
            add(observed_ns, "PLAYER_DEAD", "negative", False,
                {"player_dead": False}, {"player_dead": True})
        if current["map_exit"] and not previous["map_exit"]:
            add(observed_ns, "MAP_EXIT", "positive", True,
                {"map_exit": previous["map_exit"],
                 "episode_finished": previous["episode_finished"]},
                {"map_exit": True, "episode_finished": True})
        elif current["episode_finished"] and not previous["episode_finished"]:
            add(observed_ns, "EPISODE_FINISHED_NO_EXIT", "negative", False,
                {"episode_finished": False},
                {"episode_finished": True, "player_dead": current["player_dead"],
                 "map_exit": False})
        previous = current

    return expected


def _validate_bundle(root, research_root):
    events_path = _bundle_file(root, "events.jsonl")
    samples_path = _bundle_file(root, "scorer-samples.jsonl")
    scorer_events_path = _bundle_file(root, "scorer-events.jsonl")
    summary_path = _bundle_file(root, "scorer-summary.json")
    sources_path = _bundle_file(root, "sources.json")

    sources = _read_json(sources_path)
    _validate_sources(sources, research_root)
    events = _read_jsonl(events_path)
    samples = _read_jsonl(samples_path)
    scorer_events = _read_jsonl(scorer_events_path)
    summary = _read_json(summary_path)

    sample_ns = []
    for row in samples:
        payload = row.get("payload")
        if (not isinstance(payload, dict) or set(payload) != SAMPLE_FIELDS
                or payload.get("schema") != SAMPLE_SCHEMA
                or row.get("controller_visible") is not False):
            raise ValueError("scorer sample schema or controller isolation is invalid")
        for key in ("scheduled_ns", "sample_started_ns", "sample_finished_ns",
                    "start_lateness_ns", "missed_periods_before"):
            if type(row.get(key)) is not int:
                raise ValueError("scorer scheduler timestamp is invalid")
        if (row["sample_started_ns"] < row["scheduled_ns"]
                or row["sample_finished_ns"] < row["sample_started_ns"]
                or row["sample_started_ns"] > payload.get("sample_ns", -1)
                or payload.get("sample_ns", -1) > row["sample_finished_ns"]
                or row["start_lateness_ns"] != row["sample_started_ns"] - row["scheduled_ns"]
                or row["missed_periods_before"] < 0):
            raise ValueError("scorer sample timing bracket is invalid")
        for key in ("sample_ns", "kill_count", "death_count"):
            if type(payload.get(key)) is not int or payload[key] < 0:
                raise ValueError("scorer sample value is invalid")
        if any(type(payload.get(key)) is not bool
               for key in ("episode_finished", "player_dead", "map_exit")):
            raise ValueError("scorer sample state is invalid")
        sample_ns.append(payload["sample_ns"])
    if any(b <= a for a, b in zip(sample_ns, sample_ns[1:])):
        raise ValueError("scorer sample clock is not strictly increasing")

    previous_sequence = 0
    sample_times = set(sample_ns)
    for row in scorer_events:
        sequence = row.get("event_sequence")
        if (row.get("schema") != EVENT_SCHEMA or row.get("controller_visible") is not False
                or type(sequence) is not int or sequence <= previous_sequence
                or type(row.get("observed_ns")) is not int
                or row["observed_ns"] not in sample_times):
            raise ValueError("scorer event schema, sequence, or sample binding is invalid")
        previous_sequence = sequence
    if not _same_json_value(scorer_events, _expected_scorer_events(samples)):
        raise ValueError("scorer events do not match event-kind schema and sample transitions")

    if (summary.get("schema") != SUMMARY_SCHEMA
            or summary.get("controller_visible") is not False
            or type(summary.get("sample_count")) is not int
            or summary.get("sample_count") != len(samples)
            or type(summary.get("event_count")) is not int
            or summary.get("event_count") != len(scorer_events)
            or summary.get("event_summary") != _event_summary(scorer_events)
            or summary.get("zero_positive_events_allowed") is not True):
        raise ValueError("scorer-summary.json does not reconcile with scorer JSONL")
    scheduler = summary.get("scheduler")
    missed = scheduler.get("missed_sample_periods") if isinstance(scheduler, dict) else None
    if type(missed) is not int or missed < 0:
        raise ValueError("scorer summary scheduler record is invalid")
    if missed < sum(row["missed_periods_before"] for row in samples):
        raise ValueError("scorer summary understates missed periods in sample JSONL")
    intervals = [b - a for a, b in zip(sample_ns, sample_ns[1:])]
    if intervals:
        ordered = sorted(intervals)
        expected_intervals = {
            "median": statistics.median(intervals) / 1e6,
            "p95": ordered[min(len(ordered) - 1, round(.95 * (len(ordered) - 1)))] / 1e6,
            "max": max(intervals) / 1e6,
        }
    else:
        expected_intervals = None
    if summary.get("sample_interval_ms") != expected_intervals:
        raise ValueError("scorer summary interval statistics do not match scorer samples")
    return events, samples


def classify_run_dir(run_dir, intent_id, *, max_gap_ns, research_root=None):
    """Classify one intent only after validating all files in a run bundle.

    Directory co-location and sidecar checks prevent accidental file mixing and
    stale/malformed source metadata. They do not authenticate a bundle whose
    JSONL data and sidecars were all rewritten together.
    """
    root = Path(run_dir).resolve()
    source_root = (Path(research_root) if research_root is not None
                   else Path(__file__).resolve().parents[2])
    try:
        events, samples = _validate_bundle(root, source_root)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        return {"decision": "POST_CANCELLATION_COOCCURRENCE",
                "reason": "invalid_or_missing_run_bundle",
                "bundle_error": type(exc).__name__, "causal_attribution": False}
    return classify_intent(events, samples, intent_id, max_gap_ns=max_gap_ns)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--research-root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--intent-id", required=True)
    parser.add_argument("--max-gap-ns", required=True, type=int)
    args = parser.parse_args()
    result = classify_run_dir(args.run_dir, args.intent_id,
                              max_gap_ns=args.max_gap_ns,
                              research_root=args.research_root)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
