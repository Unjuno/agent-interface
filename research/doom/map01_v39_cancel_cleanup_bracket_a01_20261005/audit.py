"""Independent raw audit for the retained cancellation cleanup candidate."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "a02"


def main():
    errors = []
    freeze_raw = (HERE / "FREEZE-A02.json").read_bytes()
    freeze = json.loads(freeze_raw)
    source_raw = (HERE / "input_owner_v13.py").read_bytes()
    for name, expected in freeze["sources"].items():
        if hashlib.sha256((HERE / name).read_bytes()).hexdigest() != expected["sha256"]:
            errors.append(f"frozen source hash mismatch: {name}")
    event_raw = (OUT / "candidate-events.jsonl").read_bytes()
    rows = [json.loads(line) for line in event_raw.decode().splitlines() if line]
    result = json.loads((OUT / "RESULT.json").read_text(encoding="utf-8"))
    downs = {row.get("key"): row for row in rows
             if row.get("event") == "input_admission"}
    cleanup_rows = [row for row in rows if row.get("event") == "owner_release"]
    if len(downs) != 2 or set(downs) != {"a", "space"}:
        errors.append("expected two distinct per-key admissions")
    if len(cleanup_rows) != 1:
        errors.append("expected one owner cleanup record")
    cleanup = cleanup_rows[0] if len(cleanup_rows) == 1 else {}
    if cleanup.get("reason") != "cancelled" or cleanup.get("verified") is not True:
        errors.append("cleanup was not verified cancellation cleanup")
    releases = {row.get("key"): row
                for row in cleanup.get("per_key_release_measurements", [])}
    if set(releases) != {"a", "space"}:
        errors.append("cleanup key set mismatch")
    for key, release in releases.items():
        down = downs.get(key, {}).get("physical_key_measurement", {})
        interval = release.get("bracket", {}).get("physical_up_interval")
        if release.get("classification") != "CONFIRMED_PHYSICAL_UP":
            errors.append(f"{key}: cleanup up was not confirmed")
        if release.get("identity_status") != "RETIRED":
            errors.append(f"{key}: identity was not retired")
        if release.get("actuation_id") != down.get("actuation_id"):
            errors.append(f"{key}: cleanup lineage mismatch")
        if not isinstance(interval, list) or len(interval) != 2:
            errors.append(f"{key}: missing up bracket")
        else:
            pre = release.get("pre_sample", {}).get("finished_ns")
            post = release.get("post_sample", {}).get("finished_ns")
            if interval != [pre, post] or type(pre) is not int or type(post) is not int or pre > post:
                errors.append(f"{key}: sample bracket malformed")
        if release.get("grants_input_authority") is not False:
            errors.append(f"{key}: authority claim changed")
        if release.get("application_consumption_observed") is not False:
            errors.append(f"{key}: application effect claim changed")
    if result.get("raw_sha256") != hashlib.sha256(event_raw).hexdigest():
        errors.append("result/raw hash mismatch")
    if result.get("fake_physical_keys_after_cleanup") != []:
        errors.append("fake display not neutral")
    audit = {
        "run_id": freeze.get("run_id"),
        "disposition": "PASS_RECONSTRUCTED_SCOPED" if not errors else "FAIL_MISMATCH",
        "admission_count": len(downs),
        "cleanup_key_count": len(releases),
        "source_sha256": hashlib.sha256(source_raw).hexdigest(),
        "raw_sha256": hashlib.sha256(event_raw).hexdigest(),
        "errors": errors,
        "scope": "independent raw structural/lineage/bracket audit; fake display only",
    }
    (OUT / "AUDIT.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
