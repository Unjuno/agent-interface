"""Additive owner release identity auditor including nullable logical key."""
from collections import Counter

IDENTITY_FIELDS = (
    "release_id", "owner_id", "intent_token", "keycode", "key",
    "trigger_class", "reason",
)
TIME_FIELDS = (
    "request_started_ns", "request_returned_ns", "shared_sync_returned_ns",
)

def _valid_identity(row):
    for name in ("release_id", "owner_id", "intent_token", "trigger_class", "reason"):
        if not isinstance(row.get(name), str) or not row[name]:
            return False
    if type(row.get("keycode")) is not int or "key" not in row:
        return False
    key = row["key"]
    if key is not None and (not isinstance(key, str) or not key):
        return False
    return True

def _identity(row):
    return tuple(row.get(name) for name in IDENTITY_FIELDS)

def audit(expected_inventory, records):
    errors = []
    if not isinstance(expected_inventory, list) or not expected_inventory:
        return ["expected_inventory_missing_or_empty"]
    if not isinstance(records, list):
        return ["records_not_list"]

    expected_by_id = {}
    for index, item in enumerate(expected_inventory):
        if not isinstance(item, dict) or not _valid_identity(item):
            errors.append(f"expected_identity_invalid:{index}")
            continue
        release_id = item["release_id"]
        if release_id in expected_by_id:
            errors.append(f"expected_release_id_duplicate:{release_id}")
        expected_by_id[release_id] = _identity(item)

    actual_ids = []
    for index, row in enumerate(records):
        prefix = f"record:{index}"
        if not isinstance(row, dict):
            errors.append(f"{prefix}:not_object")
            continue
        if row.get("event") != "owner_key_release_bracket":
            errors.append(f"{prefix}:unexpected_event")
        if row.get("schema") != "owner-key-release-bracket-v2":
            errors.append(f"{prefix}:schema")
        missing = [name for name in IDENTITY_FIELDS + TIME_FIELDS + (
            "timing_valid", "grants_input_authority", "physical_key_up_claimed",
        ) if name not in row]
        if missing:
            errors.append(f"{prefix}:missing:{','.join(missing)}")
            continue
        if not _valid_identity(row):
            errors.append(f"{prefix}:identity_invalid")
            continue
        actual_ids.append(row["release_id"])
        for name in TIME_FIELDS:
            if type(row[name]) is not int:
                errors.append(f"{prefix}:timestamp_type:{name}")
        if all(type(row[name]) is int for name in TIME_FIELDS):
            left, middle, right = (row[name] for name in TIME_FIELDS)
            if not left <= middle <= right:
                errors.append(f"{prefix}:timestamp_order")
        if row["timing_valid"] is not True:
            errors.append(f"{prefix}:timing_valid")
        if row["grants_input_authority"] is not False:
            errors.append(f"{prefix}:authority")
        if row["physical_key_up_claimed"] is not False:
            errors.append(f"{prefix}:physical_claim")

    expected_counts = Counter(item["release_id"] for item in expected_inventory
                              if isinstance(item, dict) and _valid_identity(item))
    actual_counts = Counter(actual_ids)
    for release_id, count in expected_counts.items():
        if actual_counts[release_id] < count:
            errors.append(f"expected_release_missing:{release_id}")
        elif actual_counts[release_id] > count:
            errors.append(f"unexpected_duplicate_release:{release_id}")
    for release_id in actual_counts.keys() - expected_counts.keys():
        errors.append(f"unexpected_release:{release_id}")

    actual_by_id = {row.get("release_id"): _identity(row) for row in records
                    if isinstance(row, dict) and _valid_identity(row)}
    for release_id in actual_by_id.keys() & expected_by_id.keys():
        if actual_by_id[release_id] != expected_by_id[release_id]:
            errors.append(f"release_identity_mismatch:{release_id}")
    return errors
