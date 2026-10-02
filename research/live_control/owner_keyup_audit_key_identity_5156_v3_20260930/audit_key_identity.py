"""Fail-closed expected-inventory checker for the logical key join field."""


def _valid_expected(item):
    if not isinstance(item, dict):
        return False
    release_id = item.get("release_id")
    if type(release_id) is not str or not release_id:
        return False
    trigger = item.get("trigger_class")
    key = item.get("key", _MISSING)
    if trigger == "explicit_up":
        return type(key) is str and bool(key)
    if trigger == "owner_lease_cleanup":
        return key is None
    return False


_MISSING = object()


def audit_key_identity(expected_inventory, records):
    errors = []
    if type(expected_inventory) is not list or not expected_inventory:
        return ["expected_inventory_missing_or_invalid"]
    if type(records) is not list:
        return ["records_not_list"]

    expected = {}
    for index, item in enumerate(expected_inventory):
        if not _valid_expected(item):
            errors.append(f"expected_key_contract_invalid:{index}")
            continue
        release_id = item["release_id"]
        if release_id in expected:
            errors.append(f"expected_release_id_duplicate:{release_id}")
            continue
        expected[release_id] = (item["trigger_class"], item["key"])

    actual_counts = {}
    for index, row in enumerate(records):
        prefix = f"record:{index}"
        if type(row) is not dict:
            errors.append(f"{prefix}:not_object")
            continue
        release_id = row.get("release_id")
        if type(release_id) is not str or not release_id:
            errors.append(f"{prefix}:release_id_invalid")
            continue
        actual_counts[release_id] = actual_counts.get(release_id, 0) + 1
        if "key" not in row:
            errors.append(f"{prefix}:key_missing")
            continue
        frozen = expected.get(release_id, _MISSING)
        if frozen is _MISSING:
            errors.append(f"{prefix}:release_id_unexpected")
            continue
        trigger, expected_key = frozen
        observed_key = row["key"]
        if trigger == "explicit_up":
            if type(observed_key) is not str or not observed_key:
                errors.append(f"{prefix}:explicit_key_type_or_value")
            elif observed_key != expected_key:
                errors.append(f"{prefix}:explicit_key_mismatch")
        elif trigger == "owner_lease_cleanup":
            if observed_key is not None:
                errors.append(f"{prefix}:cleanup_key_must_be_null")
        else:
            errors.append(f"{prefix}:trigger_class_invalid")

    for release_id in expected:
        count = actual_counts.get(release_id, 0)
        if count == 0:
            errors.append(f"release_missing:{release_id}")
        elif count > 1:
            errors.append(f"release_duplicate:{release_id}")
    return errors
