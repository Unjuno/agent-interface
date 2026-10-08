"""Independent reconstruction of the frozen v10/v11 request-parity gate."""

EXPECTED_REQUEST_SEQUENCE = (
    (2, 38),
    (3, 38),
    (2, 56),
    (2, 38),
    (3, 56),
    (3, 38),
)


def _canonical_request_sequence(value):
    if type(value) is not list or len(value) != len(EXPECTED_REQUEST_SEQUENCE):
        return False
    for row in value:
        if type(row) is not list or len(row) != 2:
            return False
        if any(type(item) is not int for item in row):
            return False
    return True


def audit_owner_behavior(owner_behavior):
    """Check retained request arrays against the plan, not their summary flag."""
    if not isinstance(owner_behavior, dict):
        return ["owner_behavior_not_object"]

    errors = []
    recorded_expected = owner_behavior.get("expected_request_sequence")
    if not _canonical_request_sequence(recorded_expected):
        errors.append("expected_sequence_type_invalid")
    elif tuple(tuple(row) for row in recorded_expected) != EXPECTED_REQUEST_SEQUENCE:
        errors.append("expected_sequence_mismatch")

    sequences = []
    for name in ("v10_requests", "v11_requests"):
        value = owner_behavior.get(name)
        if not _canonical_request_sequence(value):
            errors.append("request_sequence_type_invalid")
            sequences.append(None)
            continue
        sequence = tuple(tuple(row) for row in value)
        sequences.append(sequence)
        if sequence != EXPECTED_REQUEST_SEQUENCE:
            errors.append("request_sequence_mismatch")

    v10, v11 = sequences
    request_parity = v10 is not None and v11 is not None and v10 == v11
    sync10, sync11 = owner_behavior.get("v10_sync_count"), owner_behavior.get("v11_sync_count")
    sync_parity = type(sync10) is int and type(sync11) is int and sync10 == sync11
    neutral = (owner_behavior.get("v10_final_keys_down") == []
               and owner_behavior.get("v11_final_keys_down") == [])
    derived_equivalence = request_parity and sync_parity and neutral
    if type(owner_behavior.get("v10_v11_behavior_equivalent")) is not bool:
        errors.append("equivalence_flag_type_invalid")
    elif owner_behavior["v10_v11_behavior_equivalent"] is not derived_equivalence:
        errors.append("equivalence_flag_mismatch")

    return errors
