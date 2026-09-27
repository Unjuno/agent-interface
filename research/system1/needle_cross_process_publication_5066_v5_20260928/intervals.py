"""Pure interval-reconciliation helpers for Issue #5082 construction checks."""
from __future__ import annotations

from collections.abc import Iterable, Mapping


def overlaps(left_start: int, left_end: int, right_start: int, right_end: int) -> bool:
    """Whether two half-open monotonic call intervals have positive overlap."""
    if any(type(value) is not int for value in (left_start, left_end, right_start, right_end)):
        raise TypeError("timestamps must be integers")
    if left_start > left_end or right_start > right_end:
        raise ValueError("interval start must not exceed end")
    return max(left_start, right_start) < min(left_end, right_end)


def qualifying_overlaps(
    reads: Iterable[Mapping[str, object]],
    replacements: Iterable[Mapping[str, object]],
) -> list[tuple[str, int]]:
    """Return (reader_id, read_index) for distinct read calls overlapping replace calls."""
    replace_intervals = []
    replace_ids: set[int] = set()
    for row in replacements:
        replace_index = row.get("replace_index")
        if type(replace_index) is not int or replace_index in replace_ids:
            raise ValueError("replacement indices must be unique integers")
        replace_ids.add(replace_index)
        replace_intervals.append((row["start_ns"], row["end_ns"]))
    matched: list[tuple[str, int]] = []
    for row in reads:
        reader = row["reader_id"]
        index = row["read_index"]
        pid = row.get("reader_pid")
        if not isinstance(reader, str) or type(index) is not int or type(pid) is not int:
            raise TypeError("reader_id, read_index, and reader_pid must be typed")
        if pid <= 0:
            raise ValueError("reader_pid must be positive")
        if any(overlaps(row["start_ns"], row["end_ns"], start, end)
               for start, end in replace_intervals):
            matched.append((reader, index))
    return matched


def assert_coverage(reads: Iterable[Mapping[str, object]],
                    replacements: Iterable[Mapping[str, object]],
                    minimum: int = 32, minimum_readers: int = 2) -> list[tuple[str, int]]:
    """Fail closed unless overlap denominator and independent-reader gate are met."""
    read_rows = list(reads)
    replace_rows = list(replacements)
    if len(replace_rows) != 4096:
        raise ValueError("expected exactly 4096 replacement intervals")
    if {row.get("replace_index") for row in replace_rows} != set(range(4096)):
        raise ValueError("replacement indices must cover exactly 0..4095")
    matched = qualifying_overlaps(read_rows, replace_rows)
    pid_by_reader = {row["reader_id"]: row["reader_pid"] for row in read_rows}
    reader_count = len({pid_by_reader[reader] for reader, _ in matched})
    if len(matched) < minimum or reader_count < minimum_readers:
        raise ValueError("insufficient observed read/replace interval overlaps")
    return matched
