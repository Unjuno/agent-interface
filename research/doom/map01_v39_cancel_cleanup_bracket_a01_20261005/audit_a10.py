"""Independent sample-state and operation-bracket audit for retained A03."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results/a10"
SOURCE_OUT = HERE / "results/a03"


def _int(value):
    return type(value) is int and value >= 0


def _sample_ok(sample, expected_down, label, errors, key):
    if type(sample) is not dict:
        errors.append(f"{key}: {label} sample missing")
        return None
    if sample.get("available") is not True or sample.get("error") is not None:
        errors.append(f"{key}: {label} sample unavailable or errored")
    if type(sample.get("down")) is not bool or sample.get("down") is not expected_down:
        errors.append(f"{key}: {label} sampled key state mismatch")
    started, finished = sample.get("started_ns"), sample.get("finished_ns")
    if not _int(started) or not _int(finished) or started > finished:
        errors.append(f"{key}: {label} sample interval invalid")
        return None
    return started, finished


def _edge_ok(row, edge, key, errors):
    measure = row.get("physical_key_measurement") if edge == "down" else row
    if type(measure) is not dict:
        errors.append(f"{key}: {edge} measurement missing")
        return
    pre = _sample_ok(measure.get("pre_sample"), edge == "up",
                     f"{edge} pre", errors, key)
    post = _sample_ok(measure.get("post_sample"), edge == "down",
                      f"{edge} post", errors, key)
    bracket = measure.get("bracket")
    interval_name = "physical_down_interval" if edge == "down" else "physical_up_interval"
    interval = bracket.get(interval_name) if type(bracket) is dict else None
    request_name = "press_request_ns" if edge == "down" else "release_request_ns"
    request, sync = measure.get(request_name), measure.get("sync_return_ns")
    if pre is None or post is None:
        return
    pre_started, pre_finished = pre
    post_started, post_finished = post
    if (type(interval) is not list or len(interval) != 2
            or not all(_int(value) for value in interval)
            or interval != [pre_finished, post_finished]):
        errors.append(f"{key}: {edge} bracket does not match sample endpoints")
    if not _int(request) or not _int(sync):
        errors.append(f"{key}: {edge} request/XSync timestamps missing")
    elif not (pre_started <= pre_finished <= request <= sync <= post_started <= post_finished):
        errors.append(f"{key}: {edge} request/XSync is outside ordered sample bracket")


def validate_raw(rows):
    errors = []
    admissions = {row.get("key"): row for row in rows
                  if type(row) is dict and row.get("event") == "input_admission"}
    cleanups = [row for row in rows
                if type(row) is dict and row.get("event") == "owner_release"]
    if len(admissions) != 2 or set(admissions) != {"a", "space"}:
        errors.append("expected two distinct admissions")
    if len(cleanups) != 1:
        errors.append("expected one cancellation owner-release event")
    cleanup = cleanups[0] if len(cleanups) == 1 else {}
    if cleanup.get("reason") != "cancelled" or cleanup.get("verified") is not True:
        errors.append("cleanup event is not verified cancellation cleanup")
    if cleanup.get("keys_down") != [] or cleanup.get("buttons_down") != []:
        errors.append("cleanup event is not neutral")
    releases = {row.get("key"): row for row in cleanup.get("per_key_release_measurements", [])
                if type(row) is dict}
    if set(releases) != set(admissions):
        errors.append("per-key cleanup measurement keys do not match admissions")
    for key, admission in admissions.items():
        down = admission.get("physical_key_measurement")
        release = releases.get(key)
        if type(down) is not dict or type(release) is not dict:
            errors.append(f"{key}: down or up record missing")
            continue
        if admission.get("event") != "input_admission":
            errors.append(f"{key}: admission event mismatch")
        if down.get("classification") != "CONFIRMED_PHYSICAL_DOWN":
            errors.append(f"{key}: physical down not confirmed")
        if down.get("identity_status") != "MINTED":
            errors.append(f"{key}: down actuation identity not minted")
        if release.get("classification") != "CONFIRMED_PHYSICAL_UP":
            errors.append(f"{key}: physical up not confirmed")
        if release.get("identity_status") != "RETIRED":
            errors.append(f"{key}: up actuation identity not retired")
        if release.get("actuation_id") != down.get("actuation_id"):
            errors.append(f"{key}: actuation ID cross-link mismatch")
        for record in (down, release):
            if (record.get("grants_input_authority") is not False
                    or record.get("application_consumption_observed") is not False):
                errors.append(f"{key}: measurement authority/effect boundary changed")
        _edge_ok(admission, "down", key, errors)
        _edge_ok(release, "up", key, errors)
    return errors


def audit(freeze):
    event_path = SOURCE_OUT / "candidate-events.jsonl"
    result_path = SOURCE_OUT / "RESULT.json"
    freeze_a03_path = HERE / "FREEZE-A03.json"
    source_audit_path = HERE / "audit_a03.py"
    test_path = HERE / "test_a10.py"
    expected_sources = {
        "events": event_path,
        "result": result_path,
        "freeze_a03": freeze_a03_path,
        "audit_a03": source_audit_path,
        "auditor": HERE / "audit_a10.py",
        "test": test_path,
    }
    errors = []
    for name, expected in freeze["sources"].items():
        if hashlib.sha256(expected_sources[name].read_bytes()).hexdigest() != expected:
            errors.append(f"frozen source mismatch: {name}")
    if sys.version.split()[0] != freeze.get("python_version"):
        errors.append("Python version differs from freeze")
    if errors:
        return {"schema": "map01-v39-cancel-cleanup-audit-a10",
                "run_id": freeze.get("run_id"),
                "disposition": "FAIL_FROZEN_SOURCE_MISMATCH", "errors": errors}

    raw = event_path.read_bytes()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
    result = json.loads(result_path.read_text(encoding="utf-8"))
    errors.extend(validate_raw(rows))
    if result.get("raw_sha256") != hashlib.sha256(raw).hexdigest():
        errors.append("retained A03 result/raw hash mismatch")
    if result.get("fake_physical_keys_after_cleanup") != []:
        errors.append("retained A03 result is not neutral")
    return {
        "schema": "map01-v39-cancel-cleanup-audit-a10",
        "run_id": freeze["run_id"],
        "source_run_id": result.get("run_id"),
        "disposition": "PASS_AUDITED_BRACKET_EVIDENCE" if not errors else "FAIL_MISMATCH",
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "admission_count": sum(row.get("event") == "input_admission" for row in rows),
        "owner_release_event_count": sum(row.get("event") == "owner_release"
                                          for row in rows),
        "authority_granted": False,
        "application_consumption_observed": False,
        "errors": errors,
        "scope": "sample-state and operation-bracket audit of retained fake-display cancellation trace; no live physical/game effect claim",
    }


def main():
    freeze = json.loads((HERE / "FREEZE-A10.json").read_text(encoding="utf-8"))
    value = audit(freeze)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "AUDIT.json").write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps({"disposition": value["disposition"],
                      "errors": value.get("errors", [])}, sort_keys=True))
    if value["disposition"] != "PASS_AUDITED_BRACKET_EVIDENCE":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
