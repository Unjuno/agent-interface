"""Independently validate A03 raw rows without importing the candidate."""
import json
import sys
from pathlib import Path


ALLOCATION = "5947-MULTI-UPDATE-PROVENANCE-T0-A03-20261008"
DEPTHS = {0, 1, 4, 8}
ARMS = {"CURRENT_ONLY", "FULL_CONFLICTING_HISTORY", "NONCONFLICTING_HISTORY", "SOURCE_LINKED_DELTA"}
CONDITIONS = {"current_value", "baseline_change", "unsupported"}
SLOT_SIZE = 2048
TASK_BYTES = b"select-current"
BASELINE_BYTES = b'{"source_id":"baseline/source-17","value":"old"}'
CURRENT_BYTES = b'{"source_id":"current/source-22","value":"new"}'
BASELINE_OBJECT = {"source_id": "baseline/source-17", "value": "old"}
CURRENT_OBJECT = {"source_id": "current/source-22", "value": "new"}
BASELINE_SOURCE_ID = "baseline/source-17"
CURRENT_SOURCE_ID = "current/source-22"
QUERIES = {
    "current_value": b"what-is-current-value",
    "baseline_change": b"did-value-change-from-baseline",
    "unsupported": b"unsupported-field-without-source-evidence",
}
POSITION_PREFIX = b'{"cueA":"CURRENT","cueB":"CURRENT","history":"'
SUFFIX = b'","end":"FIXTURE_ONLY"}'
MATCHED_IDENTITY_FIELDS = (
    "task_bytes", "query_bytes", "baseline_bytes", "baseline_source_id", "current_bytes",
    "current_source_id", "authority", "prefix_hex", "suffix_hex", "current_cue_offset",
    "cue_byte_length", "history_slot_start", "history_slot_end", "final_truth", "outcome",
    "answer", "reason",
)
ROW_FIELDS = {
    "allocation", "kind", "condition", "depth", "arm", "task_bytes", "query_bytes",
    "baseline_bytes", "baseline_source_id", "current_bytes", "current_source_id",
    "authority", "prefix_hex", "history_slot_hex", "suffix_hex",
    "serialized_context_hex", "history_slot_start", "history_slot_end", "lineage",
    "delta_evidence", "current_cue_offset", "cue_byte_length", "final_truth", "outcome",
    "answer", "reason",
}


def expected_prefix(condition):
    query = QUERIES[condition]
    return (
        b'{"task":"select-current","query":"' + query +
        b'","baseline":"old","baseline_source":"baseline/source-17",'
        b'"current":"new","current_source":"current/source-22",'
        b'"authority":"observation-only","CURRENT_CUE":"CURRENT","history":"'
    )


def expected_history(depth, arm):
    if arm == "CURRENT_ONLY" or depth == 0:
        return b""
    if arm == "FULL_CONFLICTING_HISTORY":
        entries = (f"episode={i};value=old{i};source=obs/{i}" for i in range(depth))
    elif arm == "NONCONFLICTING_HISTORY":
        entries = (f"episode={i};value=neutral{i};source=obs/{i}" for i in range(depth))
    elif arm == "SOURCE_LINKED_DELTA":
        entries = (f"episode={i};observed=old{i};superseded_by=current/source-22;kind=INFERRED"
                   for i in range(depth))
    else:
        return None
    return ";".join(entries).encode("ascii")


def supported_outcome(condition):
    if condition == "current_value":
        return "SYNTHETIC_SUPPORTED", "new", None
    if condition == "baseline_change":
        return "SYNTHETIC_SUPPORTED", "changed:old-to-new", None
    if condition == "unsupported":
        return "UNKNOWN_UNSUPPORTED", None, "unsupported_field_without_source_evidence"
    return None


def _decode_hex(row, field, errors, label):
    try:
        value = row[field]
        if not isinstance(value, str):
            raise TypeError("not a string")
        return bytes.fromhex(value)
    except (KeyError, TypeError, ValueError):
        errors.append(f"{label}: malformed {field}")
        return None


def _validate_row(row, index, errors):
    label = f"row[{index}]"
    if not isinstance(row, dict):
        errors.append(f"{label}: not an object")
        return None
    missing = ROW_FIELDS - set(row)
    extra = set(row) - ROW_FIELDS
    if missing:
        errors.append(f"{label}: missing fields {sorted(missing)}")
    if extra:
        errors.append(f"{label}: unexpected fields {sorted(extra)}")
    kind = row.get("kind")
    condition = row.get("condition")
    depth = row.get("depth")
    arm = row.get("arm")
    if row.get("allocation") != ALLOCATION:
        errors.append(f"{label}: allocation")
    if kind == "matched":
        if type(depth) is not int or condition not in CONDITIONS or depth not in DEPTHS or arm not in ARMS:
            errors.append(f"{label}: unexpected matched stratum")
            return None
        prefix_expected = expected_prefix(condition)
        cue_marker = b'"CURRENT_CUE":"CURRENT"'
        cue_offset_expected = prefix_expected.index(cue_marker) + len(b'"CURRENT_CUE":"')
    elif kind == "position_control":
        if type(depth) is not int or (condition, depth, arm) != ("baseline_change", 0, "CURRENT_ONLY"):
            errors.append(f"{label}: position-control stratum")
            return None
        prefix_expected = POSITION_PREFIX
        cue_offset_expected = None
    else:
        errors.append(f"{label}: unexpected row kind")
        return None

    task = _decode_hex(row, "task_bytes", errors, label)
    query = _decode_hex(row, "query_bytes", errors, label)
    baseline = _decode_hex(row, "baseline_bytes", errors, label)
    current = _decode_hex(row, "current_bytes", errors, label)
    prefix = _decode_hex(row, "prefix_hex", errors, label)
    slot = _decode_hex(row, "history_slot_hex", errors, label)
    suffix = _decode_hex(row, "suffix_hex", errors, label)
    serialized = _decode_hex(row, "serialized_context_hex", errors, label)

    if task is not None and task != TASK_BYTES:
        errors.append(f"{label}: task bytes")
    if query is not None and query != QUERIES.get(condition):
        errors.append(f"{label}: query bytes/condition")
    if prefix is not None and prefix != prefix_expected:
        errors.append(f"{label}: common prefix bytes")
    if suffix is not None and suffix != SUFFIX:
        errors.append(f"{label}: common suffix bytes")

    try:
        if baseline is None:
            raise ValueError("missing baseline")
        baseline_object = json.loads(baseline)
        if baseline != BASELINE_BYTES:
            errors.append(f"{label}: baseline exact bytes")
        if baseline_object != BASELINE_OBJECT:
            errors.append(f"{label}: baseline object")
        if baseline_object.get("source_id") != row.get("baseline_source_id"):
            errors.append(f"{label}: baseline source-id linkage")
        if row.get("baseline_source_id") != BASELINE_SOURCE_ID:
            errors.append(f"{label}: baseline source-id contract")
    except (json.JSONDecodeError, TypeError, AttributeError, ValueError):
        errors.append(f"{label}: malformed baseline object")

    try:
        if current is None:
            raise ValueError("missing current")
        current_object = json.loads(current)
        if current != CURRENT_BYTES:
            errors.append(f"{label}: current exact bytes")
        if current_object != CURRENT_OBJECT:
            errors.append(f"{label}: current object")
        if current_object.get("source_id") != row.get("current_source_id"):
            errors.append(f"{label}: current source-id linkage")
        if row.get("current_source_id") != CURRENT_SOURCE_ID:
            errors.append(f"{label}: current source-id contract")
    except (json.JSONDecodeError, TypeError, AttributeError, ValueError):
        errors.append(f"{label}: malformed current object")

    if row.get("authority") != "observation-only":
        errors.append(f"{label}: authority")
    if row.get("final_truth") != "new":
        errors.append(f"{label}: final truth")
    expected_outcome = supported_outcome(condition)
    if expected_outcome is None:
        errors.append(f"{label}: condition has no outcome contract")
    elif (row.get("outcome"), row.get("answer"), row.get("reason")) != expected_outcome:
        errors.append(f"{label}: outcome/answer/reason")

    if slot is not None:
        if len(slot) != SLOT_SIZE:
            errors.append(f"{label}: history slot length")
        history = expected_history(depth, arm)
        if history is None:
            errors.append(f"{label}: history arm")
        elif slot != history + b" " * (SLOT_SIZE - len(history)):
            errors.append(f"{label}: history bytes/lineage")
    lineage = row.get("lineage")
    if (not isinstance(lineage, list) or any(type(item) is not int for item in lineage) or
            lineage != list(range(depth))):
        errors.append(f"{label}: lineage")
    expected_delta = "INFERRED" if arm == "SOURCE_LINKED_DELTA" and depth else "NONE"
    if row.get("delta_evidence") != expected_delta:
        errors.append(f"{label}: delta evidence")

    if prefix is not None and slot is not None and suffix is not None:
        prefix_length = len(prefix)
        if row.get("history_slot_start") != prefix_length:
            errors.append(f"{label}: history start")
        if row.get("history_slot_end") != prefix_length + len(slot):
            errors.append(f"{label}: history end")
        if serialized is not None and serialized != prefix + slot + suffix:
            errors.append(f"{label}: serialized context reconstruction")
    elif serialized is not None:
        errors.append(f"{label}: serialized context lacks reconstructable components")

    if row.get("cue_byte_length") != len(b"CURRENT"):
        errors.append(f"{label}: cue byte length")
    cue_offset = row.get("current_cue_offset")
    if kind == "matched":
        if cue_offset_expected is not None and cue_offset != cue_offset_expected:
            errors.append(f"{label}: matched cue offset")
        if prefix is not None and isinstance(cue_offset, int):
            if prefix[cue_offset:cue_offset + len(b"CURRENT")] != b"CURRENT":
                errors.append(f"{label}: matched cue slice")
        return row

    occurrences = []
    start = 0
    while True:
        position = POSITION_PREFIX.find(b'"CURRENT"', start)
        if position < 0:
            break
        occurrences.append(position + 1)
        start = position + len(b'"CURRENT"')
    if occurrences != [9, 26]:
        errors.append(f"{label}: frozen position-control fixture offsets")
    if cue_offset not in occurrences:
        errors.append(f"{label}: position cue offset")
    if prefix is not None and isinstance(cue_offset, int):
        if prefix[cue_offset:cue_offset + len(b"CURRENT")] != b"CURRENT":
            errors.append(f"{label}: position cue slice")
    return row


def audit_rows(rows):
    errors = []
    if not isinstance(rows, list):
        return {"result": "FAIL", "matched_rows": 0, "position_rows": 0, "errors": ["top-level is not a list"]}
    if len(rows) != 50:
        errors.append("total row count")
    matched = [row for row in rows if isinstance(row, dict) and row.get("kind") == "matched"]
    positions = [row for row in rows if isinstance(row, dict) and row.get("kind") == "position_control"]
    if len(matched) != 48:
        errors.append("matched row count")
    if len(positions) != 2:
        errors.append("position row count")

    checked = [_validate_row(row, index, errors) for index, row in enumerate(rows)]
    groups = {}
    for row in matched:
        if row.get("condition") in CONDITIONS and row.get("depth") in DEPTHS:
            groups.setdefault((row["condition"], row["depth"]), []).append(row)
    expected_groups = {(condition, depth) for condition in CONDITIONS for depth in DEPTHS}
    if set(groups) != expected_groups:
        errors.append("matched group set")
    for key, group in groups.items():
        if len(group) != 4 or {row.get("arm") for row in group} != ARMS:
            errors.append(f"matched arm coverage {key}")
        for field in MATCHED_IDENTITY_FIELDS:
            if len({row.get(field) for row in group}) != 1:
                errors.append(f"matched identity {key}:{field}")
        try:
            if len({len(bytes.fromhex(row["serialized_context_hex"])) for row in group}) != 1:
                errors.append(f"matched context byte budget {key}")
        except (KeyError, TypeError, ValueError):
            errors.append(f"matched context byte budget parse {key}")

    if len(positions) == 2:
        offsets = [row.get("current_cue_offset") for row in positions]
        if offsets != [9, 26]:
            errors.append("position positive-control offsets")
        differences = {field for field in set(positions[0]) | set(positions[1])
                       if positions[0].get(field) != positions[1].get(field)}
        if differences != {"current_cue_offset"}:
            errors.append("position positive-control changed extra fields")

    return {"result": "PASS" if not errors else "FAIL", "matched_rows": len(matched),
            "position_rows": len(positions), "errors": errors}


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: auditor.py RAW.json RESULT.json")
    raw_path, result_path = Path(argv[1]), Path(argv[2])
    if result_path.exists():
        raise SystemExit("STOP: audit output already exists")
    try:
        rows = json.loads(raw_path.read_text(encoding="utf-8"))
        result = audit_rows(rows)
    except (OSError, json.JSONDecodeError) as error:
        result = {"result": "FAIL", "matched_rows": 0, "position_rows": 0,
                  "errors": ["cannot read raw JSON: " + type(error).__name__]}
    result_path.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n",
                           encoding="utf-8")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if result["result"] == "PASS" else 1)


if __name__ == "__main__":
    main(sys.argv)
