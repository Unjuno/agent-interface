"""Independent interval validator; intentionally does not import intervals.py."""
from __future__ import annotations

from collections.abc import Iterable, Mapping


def audit_overlap_rows(reads: Iterable[Mapping[str, object]],
                       replacements: Iterable[Mapping[str, object]]) -> dict[str, object]:
    read_rows = list(reads)
    replace_rows = list(replacements)
    errors: list[str] = []
    if len(replace_rows) != 4096:
        errors.append("replacement_count")
    replace_spans: list[tuple[int, int]] = []
    replace_ids: set[int] = set()
    for row in replace_rows:
        start, end = row.get("start_ns"), row.get("end_ns")
        index = row.get("replace_index")
        if (type(start) is not int or type(end) is not int or start >= end or
                type(index) is not int or index in replace_ids):
            errors.append("invalid_replace_interval")
            continue
        replace_ids.add(index)
        replace_spans.append((start, end))
    if replace_ids != set(range(4096)):
        errors.append("replacement_index_coverage")
    unique_keys: set[tuple[str, int]] = set()
    overlaps: list[tuple[str, int]] = []
    pid_by_reader: dict[str, int] = {}
    for row in read_rows:
        reader, index = row.get("reader_id"), row.get("read_index")
        start, end = row.get("start_ns"), row.get("end_ns")
        pid = row.get("reader_pid")
        if (not isinstance(reader, str) or type(index) is not int or
                type(start) is not int or type(end) is not int or start >= end or
                type(pid) is not int or pid <= 0):
            errors.append("invalid_read_interval")
            continue
        if reader in pid_by_reader and pid_by_reader[reader] != pid:
            errors.append("reader_pid_changed")
            continue
        pid_by_reader[reader] = pid
        key = (reader, index)
        if key in unique_keys:
            errors.append("duplicate_read_identity")
            continue
        unique_keys.add(key)
        if any(max(start, left) < min(end, right) for left, right in replace_spans):
            overlaps.append(key)
    if len(overlaps) < 32:
        errors.append("overlap_count_below_threshold")
    if len({pid_by_reader[reader] for reader, _ in overlaps}) < 2:
        errors.append("overlaps_from_fewer_than_two_readers")
    return {"errors": errors, "read_count": len(read_rows),
            "replacement_count": len(replace_rows), "overlap_count": len(overlaps),
            "overlap_readers": sorted({reader for reader, _ in overlaps})}
