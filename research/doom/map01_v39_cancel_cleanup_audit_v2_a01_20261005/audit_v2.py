"""Supplemental raw-only validation for cancellation-cleanup A03 brackets.

The original A03 auditor remains an immutable historical artifact. This
version reconstructs sample state and chronology from the retained event rows.
"""
import hashlib
import json

SCHEMA = "map01-v39-cancel-cleanup-audit-v2-a01"
PASS = "PASS_RECONSTRUCTED_SCOPED"
FAIL = "FAIL_MISMATCH"


def _exact_ns(value):
    return type(value) is int and value >= 0


def _exact_interval(value, expected):
    return (
        type(value) is list
        and len(value) == 2
        and all(_exact_ns(item) for item in value)
        and value == expected
    )


def _sample(sample, *, down, label, errors):
    if type(sample) is not dict:
        errors.append(f"{label}: sample is not an object")
        return None, None
    if sample.get("available") is not True:
        errors.append(f"{label}: sample unavailable")
    if type(sample.get("down")) is not bool or sample.get("down") is not down:
        errors.append(f"{label}: sampled down state mismatch")
    if sample.get("error") is not None:
        errors.append(f"{label}: sample reports an error")
    started = sample.get("started_ns")
    finished = sample.get("finished_ns")
    if not _exact_ns(started) or not _exact_ns(finished):
        errors.append(f"{label}: sample timestamps are not exact nonnegative integers")
        return None, None
    if started > finished:
        errors.append(f"{label}: sample chronology is reversed")
    return started, finished


def audit_raw(raw_bytes, result_bytes):
    """Return a deterministic raw-audit report without rewriting evidence."""
    errors = []
    rows = []
    result = {}
    try:
        for line_number, line in enumerate(raw_bytes.splitlines(), 1):
            if not line:
                continue
            row = json.loads(line)
            if type(row) is not dict:
                errors.append(f"event line {line_number}: row is not an object")
                continue
            rows.append(row)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"raw JSONL cannot be parsed: {type(exc).__name__}")
    try:
        parsed_result = json.loads(result_bytes)
        if type(parsed_result) is dict:
            result = parsed_result
        else:
            errors.append("result root is not an object")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"result JSON cannot be parsed: {type(exc).__name__}")

    raw_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    if result.get("raw_sha256") != raw_sha256:
        errors.append("result/raw hash mismatch")

    admissions = {}
    for position, row in enumerate(rows):
        if row.get("event") != "input_admission":
            continue
        key = row.get("key")
        if type(key) is not str or not key:
            errors.append(f"admission {position}: key is invalid")
            continue
        if key in admissions:
            errors.append(f"admission {position}: duplicate key")
            continue
        measure = row.get("physical_key_measurement")
        if type(measure) is not dict:
            errors.append(f"admission {key}: measurement is missing")
            continue
        actuation_id = measure.get("actuation_id")
        if type(actuation_id) is not str or not actuation_id:
            errors.append(f"admission {key}: actuation identity is invalid")
            continue
        if measure.get("classification") != "CONFIRMED_PHYSICAL_DOWN":
            errors.append(f"admission {key}: down classification mismatch")
        admissions[key] = {"position": position, "actuation_id": actuation_id}

    cleanup_rows = [row for row in rows if row.get("event") == "owner_release"]
    if len(cleanup_rows) != 1:
        errors.append("expected exactly one owner cleanup record")
    cleanup = cleanup_rows[0] if len(cleanup_rows) == 1 else {}
    if cleanup.get("reason") != "cancelled" or cleanup.get("verified") is not True:
        errors.append("cleanup is not verified cancellation cleanup")
    if cleanup.get("keys_down") != [] or cleanup.get("buttons_down") != []:
        errors.append("cleanup did not report neutral owner state")
    cleanup_position = rows.index(cleanup) if cleanup else -1
    for key, admission in admissions.items():
        if admission["position"] >= cleanup_position:
            errors.append(f"admission {key}: occurs after cleanup")

    release_rows = cleanup.get("per_key_release_measurements", [])
    if type(release_rows) is not list:
        errors.append("per-key release measurements are not a list")
        release_rows = []
    releases = {}
    for index, release in enumerate(release_rows):
        if type(release) is not dict:
            errors.append(f"release {index}: row is not an object")
            continue
        key = release.get("key")
        if type(key) is not str or not key:
            errors.append(f"release {index}: key is invalid")
            continue
        if key in releases:
            errors.append(f"release {key}: duplicate release")
            continue
        releases[key] = release
        admission = admissions.get(key)
        if admission is None:
            errors.append(f"release {key}: no matching admission")
        elif release.get("actuation_id") != admission["actuation_id"]:
            errors.append(f"release {key}: actuation lineage mismatch")
        if release.get("classification") != "CONFIRMED_PHYSICAL_UP":
            errors.append(f"release {key}: up classification mismatch")
        if release.get("identity_status") != "RETIRED" or release.get("edge") != "up":
            errors.append(f"release {key}: actuation was not retired by up")
        if release.get("release_attempted") is not True:
            errors.append(f"release {key}: release was not attempted")

        pre_start, pre_finish = _sample(
            release.get("pre_sample"), down=True, label=f"release {key} pre", errors=errors)
        post_start, post_finish = _sample(
            release.get("post_sample"), down=False, label=f"release {key} post", errors=errors)
        request_ns = release.get("release_request_ns")
        sync_ns = release.get("sync_return_ns")
        if not _exact_ns(request_ns) or not _exact_ns(sync_ns):
            errors.append(f"release {key}: release/sync timestamps are not exact nonnegative integers")
        elif pre_finish is not None and post_start is not None and post_finish is not None:
            if not (pre_finish <= request_ns <= sync_ns <= post_start <= post_finish):
                errors.append(f"release {key}: request/sync is outside the ordered sample bracket")

        expected_interval = [pre_finish, post_finish]
        bracket = release.get("bracket")
        if type(bracket) is not dict:
            errors.append(f"release {key}: nested bracket is missing")
            bracket = {}
        interval = bracket.get("physical_up_interval")
        if pre_finish is None or post_finish is None or not _exact_interval(interval, expected_interval):
            errors.append(f"release {key}: nested up interval does not match exact sample endpoints")
        if bracket.get("key") != key or bracket.get("cleanup_reason") != "cancelled":
            errors.append(f"release {key}: nested release identity/reason mismatch")
        if bracket.get("status") != "CONFIRMED_PHYSICAL_UP":
            errors.append(f"release {key}: nested up status mismatch")
        if bracket.get("actuation_id") not in (None, release.get("actuation_id")):
            errors.append(f"release {key}: nested actuation identity mismatch")
        for field, object_value in (("grants_input_authority", release),
                                    ("application_consumption_observed", release),
                                    ("grants_input_authority", bracket),
                                    ("application_consumption_observed", bracket)):
            if object_value.get(field) is not False:
                errors.append(f"release {key}: {field} must remain false")

    if set(admissions) != set(releases):
        errors.append("admission/release key sets differ")
    if len(admissions) != 2 or set(admissions) != {"a", "space"}:
        errors.append("expected exactly the two frozen admissions")
    if result.get("admission_count") != len(admissions):
        errors.append("result admission count mismatch")
    if result.get("measurement_keys") != sorted(admissions):
        errors.append("result measurement key set mismatch")
    if result.get("cleanup_verified") is not True or result.get("fake_physical_keys_after_cleanup") != []:
        errors.append("result does not record verified neutral cleanup")
    if result.get("authority_granted") is not False or result.get("application_consumption_observed") is not False:
        errors.append("result authority/consumption scope changed")

    return {
        "schema": SCHEMA,
        "run_id": result.get("run_id"),
        "disposition": PASS if not errors else FAIL,
        "admission_count": len(admissions),
        "release_count": len(releases),
        "raw_sha256": raw_sha256,
        "errors": errors,
        "scope": "supplemental raw audit of fake-display state samples, per-key release chronology, and identity only",
    }


if __name__ == "__main__":
    from pathlib import Path
    here = Path(__file__).resolve().parent
    raw = (here / "fixtures" / "candidate-events.jsonl").read_bytes()
    result = (here / "fixtures" / "RESULT.json").read_bytes()
    report = audit_raw(raw, result)
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["disposition"] == PASS else 1)
