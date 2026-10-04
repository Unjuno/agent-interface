"""Strict raw-only integrity audit for retained A03 per-key cleanup evidence."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
SOURCE_OUT = PARENT / "results" / "a03"
OUT = HERE / "results" / "a11"


def validate_raw(rows):
    errors = []
    admissions_list = [
        row for row in rows
        if type(row) is dict and row.get("event") == "input_admission"
    ]
    if len(admissions_list) != 2:
        errors.append("expected exactly two input_admission rows")
    admission_keys = [row.get("key") for row in admissions_list]
    if any(type(key) is not str for key in admission_keys):
        errors.append("input_admission key is not a string")
    valid_admission_keys = [key for key in admission_keys if type(key) is str]
    if len(set(valid_admission_keys)) != len(valid_admission_keys):
        errors.append("duplicate input_admission key")
    if set(valid_admission_keys) != {"a", "space"}:
        errors.append("expected admission keys a and space")
    admissions = {
        row.get("key"): row for row in admissions_list
        if type(row.get("key")) is str
    }

    cleanups = [
        row for row in rows
        if type(row) is dict and row.get("event") == "owner_release"
    ]
    if len(cleanups) != 1:
        errors.append("expected one cancellation owner_release row")
    cleanup = cleanups[0] if len(cleanups) == 1 else {}
    if cleanup.get("reason") != "cancelled" or cleanup.get("verified") is not True:
        errors.append("cleanup event is not verified cancellation cleanup")
    if cleanup.get("keys_down") != [] or cleanup.get("buttons_down") != []:
        errors.append("cleanup event is not neutral")

    release_list = cleanup.get("per_key_release_measurements")
    if type(release_list) is not list:
        errors.append("per-key release measurements are not a list")
        release_list = []
    if len(release_list) != len(admissions_list):
        errors.append("per-key release row count does not match admission row count")
    release_keys = [
        row.get("key") for row in release_list if type(row) is dict
    ]
    if len(release_keys) != len(release_list):
        errors.append("malformed per-key release row")
    if any(type(key) is not str for key in release_keys):
        errors.append("per-key release key is not a string")
    valid_release_keys = [key for key in release_keys if type(key) is str]
    if len(set(valid_release_keys)) != len(valid_release_keys):
        errors.append("duplicate per-key release key")
    if set(valid_release_keys) != set(valid_admission_keys):
        errors.append("per-key release keys do not exactly match admission keys")
    releases = {
        row.get("key"): row for row in release_list
        if type(row) is dict and type(row.get("key")) is str
    }

    down_ids = []
    release_ids = []
    for key, admission in admissions.items():
        down = admission.get("physical_key_measurement")
        release = releases.get(key)
        if type(down) is not dict or type(release) is not dict:
            errors.append(f"{key}: down or up record missing")
            continue
        actuation_id = down.get("actuation_id")
        down_ids.append(actuation_id)
        release_ids.append(release.get("actuation_id"))
        if down.get("classification") != "CONFIRMED_PHYSICAL_DOWN":
            errors.append(f"{key}: physical down not confirmed")
        if down.get("identity_status") != "MINTED":
            errors.append(f"{key}: down actuation identity not minted")
        if release.get("classification") != "CONFIRMED_PHYSICAL_UP":
            errors.append(f"{key}: physical up not confirmed")
        if release.get("identity_status") != "RETIRED":
            errors.append(f"{key}: up actuation identity not retired")
        if release.get("release_attempted") is not True:
            errors.append(f"{key}: cleanup release was not explicitly attempted")
        if not isinstance(actuation_id, str) or not actuation_id:
            errors.append(f"{key}: missing down actuation ID")
        if release.get("actuation_id") != actuation_id:
            errors.append(f"{key}: cleanup lineage mismatch")
        for record in (down, release):
            if (record.get("grants_input_authority") is not False
                    or record.get("application_consumption_observed") is not False):
                errors.append(f"{key}: authority/effect boundary changed")

    if (len(down_ids) != len(admissions_list)
            or any(not isinstance(value, str) or not value for value in down_ids)
            or len(set(down_ids)) != len(down_ids)):
        errors.append("admission actuation IDs are missing or non-unique")
    if (len(release_ids) != len(release_list)
            or any(not isinstance(value, str) or not value for value in release_ids)
            or len(set(release_ids)) != len(release_ids)):
        errors.append("release actuation IDs are missing or non-unique")
    return errors


def audit(freeze):
    raw_path = SOURCE_OUT / "candidate-events.jsonl"
    result_path = SOURCE_OUT / "RESULT.json"
    source_paths = {
        "events": raw_path,
        "result": result_path,
        "freeze_a03": PARENT / "FREEZE-A03.json",
        "audit_a03": PARENT / "audit_a03.py",
        "readme": HERE / "README.md",
        "auditor": HERE / "audit_a11.py",
        "test": HERE / "test_a11.py",
    }
    errors = []
    for name, expected in freeze["sources"].items():
        actual = hashlib.sha256(source_paths[name].read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"frozen source mismatch: {name}")
    if sys.version.split()[0] != freeze.get("python_version"):
        errors.append("Python version differs from freeze")
    if errors:
        return {
            "run_id": freeze.get("run_id"),
            "disposition": "FAIL_FROZEN_SOURCE_MISMATCH",
            "errors": errors,
        }

    raw = raw_path.read_bytes()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
    result = json.loads(result_path.read_text(encoding="utf-8"))
    errors.extend(validate_raw(rows))
    if result.get("raw_sha256") != hashlib.sha256(raw).hexdigest():
        errors.append("retained A03 result/raw hash mismatch")
    if result.get("fake_physical_keys_after_cleanup") != []:
        errors.append("retained A03 result is not neutral")
    return {
        "run_id": freeze["run_id"],
        "source_run_id": result.get("run_id"),
        "disposition": "PASS_AUDITED_CLEANUP_INTEGRITY" if not errors else "FAIL_MISMATCH",
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "admission_count": sum(row.get("event") == "input_admission" for row in rows),
        "release_measurement_count": sum(
            len(row.get("per_key_release_measurements", []))
            for row in rows if row.get("event") == "owner_release"
        ),
        "authority_granted": False,
        "application_consumption_observed": False,
        "errors": errors,
        "scope": "raw-only duplicate, identity and explicit-release integrity audit over retained fake-display evidence",
    }


def main():
    freeze = json.loads((HERE / "FREEZE-A11.json").read_text(encoding="utf-8"))
    value = audit(freeze)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "AUDIT.json").write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(json.dumps({"disposition": value["disposition"], "errors": value.get("errors", [])},
                     sort_keys=True))
    if value["disposition"] != "PASS_AUDITED_CLEANUP_INTEGRITY":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
