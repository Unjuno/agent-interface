"""Independent raw-only audit; standard-library only, no candidate imports."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOOM = HERE.parents[1]
RESULTS = HERE / "results" / "formal-01"
FREEZE = HERE / "FREEZE.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(raw: dict) -> list[str]:
    errors: list[str] = []
    if raw.get("schema") != "map01-scorer-command-wait-construction-raw-v1":
        errors.append("raw_schema")
    if raw.get("candidate_exit_code") != 0:
        errors.append("candidate_exit")
    if raw.get("writer_errors") != []:
        errors.append("writer_error")
    if raw.get("returned_line") != raw.get("requested_command"):
        errors.append("command_changed_or_mixed")
    sent, wait_start = raw.get("command_sent_ns"), raw.get("wait_started_ns")
    if type(sent) is not int or type(wait_start) is not int or sent <= wait_start:
        errors.append("wait_bracket")
    received = raw.get("command_received_ns")
    if type(received) is not int or type(sent) is not int or received < sent:
        errors.append("command_receive_order")

    samples = raw.get("samples")
    events = raw.get("events")
    scheduler = raw.get("scheduler")
    if not isinstance(samples, list) or len(samples) < 3:
        errors.append("sample_count")
        samples = samples if isinstance(samples, list) else []
    if not isinstance(events, list):
        errors.append("events_not_list")
        events = []
    if not isinstance(scheduler, dict) or scheduler.get("samples") != len(samples):
        errors.append("scheduler_sample_count")
    if any(row.get("controller_visible") is not False for row in samples if isinstance(row, dict)):
        errors.append("sample_authority")
    for sample in samples:
        if not isinstance(sample, dict) or not isinstance(sample.get("payload"), dict):
            errors.append("sample_shape")
            continue
        if sample.get("payload", {}).get("schema") != "independent-progress-sample-v2":
            errors.append("sample_schema")
    if any(event.get("controller_visible") is not False for event in events if isinstance(event, dict)):
        errors.append("event_authority")
    if any(not isinstance(event, dict) or event.get("schema") != "independent-progress-event-v2"
           for event in events):
        errors.append("event_schema")

    inventory = [(event.get("kind"), event.get("polarity"), event.get("useful"))
                 for event in events if isinstance(event, dict)]
    expected = [
        ("KILL_COUNT_INCREASE", "positive", True),
        ("DEATH_COUNT_INCREASE", "negative", False),
    ]
    if sorted(inventory) != sorted(expected):
        errors.append("event_inventory")
    for event in events:
        if not isinstance(event, dict):
            continue
        observed = event.get("observed_ns")
        if type(observed) is not int or type(wait_start) is not int or type(sent) is not int \
                or not (wait_start < observed < sent):
            errors.append("event_outside_command_wait")
    return sorted(set(errors))


def main() -> int:
    if not RESULTS.exists():
        raise SystemExit("STOP_NO_CANDIDATE_OUTPUT")
    expected_hashes = json.loads(FREEZE.read_text(encoding="utf-8"))["pinned_sha256"]
    source_errors = []
    for relative, expected in expected_hashes.items():
        path = (DOOM / relative.removeprefix("components/")) if relative.startswith("components/") else HERE / relative
        if digest(path) != expected:
            source_errors.append(f"source_hash:{relative}")
    run_path, raw_path = RESULTS / "RUN.json", RESULTS / "RAW.json"
    run_bytes, raw_bytes = run_path.read_bytes(), raw_path.read_bytes()
    run, raw = json.loads(run_bytes), json.loads(raw_bytes)
    if raw.get("pinned_sha256") != expected_hashes:
        source_errors.append("raw_source_inventory")
    if hashlib.sha256(raw_bytes).hexdigest() != run.get("raw_sha256"):
        source_errors.append("raw_receipt_hash")
    if raw.get("freeze_sha256") != digest(FREEZE):
        source_errors.append("freeze_hash")
    if raw.get("candidate_sha256") != digest(HERE / "candidate.py"):
        source_errors.append("candidate_hash")
    errors = source_errors + evaluate(raw)

    mutations = {}

    def visible_mutation(value: dict) -> None:
        if value["events"]:
            value["events"][0]["controller_visible"] = True
        else:
            value["events"].append({"controller_visible": True})

    def late_event_mutation(value: dict) -> None:
        if value["events"]:
            value["events"][0]["observed_ns"] = value["command_sent_ns"] + 1
        else:
            value["events"].append({"observed_ns": value["command_sent_ns"] + 1})

    for name, mutate in (
        ("omitted_event", lambda x: x["events"].pop() if x["events"] else None),
        ("controller_visible", visible_mutation),
        ("event_after_wait", late_event_mutation),
    ):
        altered = copy.deepcopy(raw)
        mutate(altered)
        mutation_errors = evaluate(altered)
        mutations[name] = {"rejected": bool(mutation_errors), "errors": mutation_errors}
        if not mutation_errors:
            errors.append(f"mutation_accepted:{name}")

    result = {
        "schema": "map01-scorer-command-wait-construction-audit-v1",
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "source_errors": source_errors,
        "raw_errors": evaluate(raw),
        "mutations": mutations,
        "status": "PASS_SCORER_EVENTS_RETAINED_DURING_COMMAND_WAIT_CONSTRUCTION" if not errors else "FAIL_AUDIT",
        "errors": sorted(set(errors)),
        "scope": "host construction only; no MAP01, model, X11, Docker, plan/actuation binding, or causal efficacy claim",
    }
    (RESULTS / "AUDIT.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
