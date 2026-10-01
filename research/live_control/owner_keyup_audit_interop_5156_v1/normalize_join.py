"""Fail-closed construction join from owner-v1 rows to completeness-v2 rows."""
from collections import Counter, defaultdict
from copy import deepcopy


class JoinError(ValueError):
    pass


def normalize_join(expected_inventory, owner_rows, caller_receipts):
    """Bind source-shaped rows to independent IDs, checking receipts first.

    This deliberately accepts only frozen inventory identities and v1/v3
    contracts. It never invents timestamps, authority, or physical state.
    """
    if not isinstance(expected_inventory, list) or not expected_inventory:
        raise JoinError("expected_inventory_empty")
    if not isinstance(owner_rows, list) or not isinstance(caller_receipts, list):
        raise JoinError("inputs_not_lists")

    identity_fields = ("owner_id", "intent_token", "keycode", "trigger_class", "reason")

    def identity(item):
        return tuple(item.get(name) for name in identity_fields)

    def valid_identity(item):
        return (
            isinstance(item, dict)
            and all(isinstance(item.get(name), str) and item[name]
                    for name in ("owner_id", "intent_token", "trigger_class", "reason"))
            and type(item.get("keycode")) is int
        )

    expected_by_identity = defaultdict(list)
    seen_ids = set()
    for index, item in enumerate(expected_inventory):
        if not valid_identity(item) or not isinstance(item.get("release_id"), str) or not item["release_id"]:
            raise JoinError(f"expected_identity_invalid:{index}")
        if type(item.get("sequence")) is not int or item["sequence"] < 1:
            raise JoinError(f"expected_sequence_invalid:{index}")
        if item["release_id"] in seen_ids:
            raise JoinError(f"expected_release_id_duplicate:{item['release_id']}")
        if "key" not in item:
            raise JoinError(f"expected_key_missing:{index}")
        seen_ids.add(item["release_id"])
        expected_by_identity[identity(item)].append(item)

    for key, items in expected_by_identity.items():
        sequences = sorted(item["sequence"] for item in items)
        if sequences != list(range(1, len(items) + 1)):
            raise JoinError(f"expected_sequence_invalid:{key}")
        if len({item["key"] for item in items}) != 1:
            raise JoinError(f"expected_key_ambiguous:{key}")
        items.sort(key=lambda item: item["sequence"])

    raw = []
    for index, row in enumerate(owner_rows):
        if not isinstance(row, dict):
            raise JoinError(f"owner_record_not_object:{index}")
        if row.get("event") != "owner_key_release_bracket":
            continue
        if row.get("schema") != "owner-key-release-bracket-v1" or not valid_identity(row):
            raise JoinError(f"owner_row_schema_or_identity_invalid:{index}")
        if row.get("timing_valid") is not True:
            raise JoinError(f"owner_timing_invalid:{index}")
        if row.get("grants_input_authority") is not False or row.get("physical_key_up_claimed") is not False:
            raise JoinError(f"unsafe_claim:{index}")
        times = (row.get("request_started_ns"), row.get("request_returned_ns"),
                 row.get("shared_sync_returned_ns"))
        if any(type(value) is not int for value in times) or not times[0] <= times[1] <= times[2]:
            raise JoinError(f"owner_interval_invalid:{index}")
        raw.append(row)

    raw_by_identity = defaultdict(list)
    for row in raw:
        raw_by_identity[identity(row)].append(row)
    if Counter({key: len(value) for key, value in raw_by_identity.items()}) != \
       Counter({key: len(value) for key, value in expected_by_identity.items()}):
        raise JoinError("owner_release_count_mismatch")
    for key, rows in raw_by_identity.items():
        if any(row.get("key") != expected_by_identity[key][0]["key"] for row in rows):
            raise JoinError(f"owner_key_identity_mismatch:{key}")

    explicit_identities = {key for key in expected_by_identity if key[3] == "explicit_up"}
    receipts_by_identity = defaultdict(list)
    for index, receipt in enumerate(caller_receipts):
        if not isinstance(receipt, dict):
            raise JoinError(f"caller_record_not_object:{index}")
        if receipt.get("event") != "input_release_transition":
            continue
        if receipt.get("operation") != "up":
            raise JoinError(f"caller_operation_unsupported:{index}")
        if receipt.get("transition_schema") != "input-release-transition-v3":
            raise JoinError(f"caller_schema_invalid:{index}")
        if receipt.get("grants_input_authority") is not False:
            raise JoinError(f"unsafe_caller_claim:{index}")
        start, end = receipt.get("release_call_started_ns"), receipt.get("release_call_returned_ns")
        if type(start) is not int or type(end) is not int or start > end:
            raise JoinError(f"caller_interval_invalid:{index}")
        if not all(isinstance(receipt.get(name), str) and receipt[name]
                   for name in ("owner_id", "intent_token", "key")):
            raise JoinError(f"caller_identity_invalid:{index}")
        receipt_key = (receipt["owner_id"], receipt["intent_token"], receipt["key"])
        receipts_by_identity[receipt_key].append(receipt)

    explicit_keys = Counter((key[0], key[1], expected_by_identity[key][0]["key"])
                            for key in explicit_identities
                            for _ in expected_by_identity[key])
    receipt_counts = Counter({key: len(value) for key, value in receipts_by_identity.items()})
    if explicit_keys != receipt_counts:
        raise JoinError("caller_receipt_count_mismatch")

    release_id_by_object = {}
    for key, expected_items in expected_by_identity.items():
        rows = raw_by_identity[key]
        if key[3] == "explicit_up":
            receipt_key = (key[0], key[1], expected_items[0]["key"])
            receipts = receipts_by_identity[receipt_key]
            pairs = []
            for row in rows:
                owner_times = (row["request_started_ns"], row["request_returned_ns"],
                               row["shared_sync_returned_ns"])
                candidates = [receipt for receipt in receipts
                              if receipt["release_call_started_ns"] <= owner_times[0]
                              and owner_times[1] <= owner_times[2]
                              and owner_times[2] <= receipt["release_call_returned_ns"]]
                if len(candidates) != 1:
                    raise JoinError("caller_pairing_ambiguous" if candidates else "caller_pairing_missing")
                pairs.append((row, candidates[0]))
            if len({id(receipt) for _, receipt in pairs}) != len(pairs):
                raise JoinError("caller_receipt_reused")
            pairs.sort(key=lambda pair: pair[1]["release_call_started_ns"])
            if any(pairs[i][1]["release_call_returned_ns"] >
                   pairs[i + 1][1]["release_call_started_ns"] for i in range(len(pairs) - 1)):
                raise JoinError("caller_pairing_ambiguous")
            for item, (row, receipt) in zip(expected_items, pairs):
                release_id_by_object[id(row)] = (item["release_id"], receipt)
        else:
            if key[3] not in ("owner_lease_cleanup", "owner_stop", "thread_finalizer"):
                raise JoinError(f"release_trigger_unclassified:{key[3]}")
            rows.sort(key=lambda row: row["request_started_ns"])
            for item, row in zip(expected_items, rows):
                release_id_by_object[id(row)] = (item["release_id"], None)

    normalized = []
    for row in raw:
        release_id, receipt = release_id_by_object[id(row)]
        result = deepcopy(row)
        result["schema"] = "owner-key-release-bracket-v2"
        result["release_id"] = release_id
        if receipt is not None:
            result["caller_started_ns"] = receipt["release_call_started_ns"]
            result["caller_returned_ns"] = receipt["release_call_returned_ns"]
        normalized.append(result)
    return normalized
