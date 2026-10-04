"""Research tail compatibility wrapper for shared bounded input expansion."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.core_v1.sequence import expand_text_gaps


def expand_tail(tail, *, max_ops):
    if type(max_ops) is not int or not 0 <= max_ops <= 126:
        raise ValueError('native tail capacity must be 0..126')
    return expand_text_gaps(tail, max_ops=max_ops)[0]


def paced_text_tail(ops, gap_ms):
    """Set a research default; explicit per-operation pacing takes precedence."""
    if type(gap_ms) is not int or gap_ms not in (0, 2, 10):
        raise ValueError("supported text gaps are 0, 2, 10 ms")
    result = []
    for op in ops:
        if not isinstance(op, dict):
            raise ValueError("operation must be an object")
        item = dict(op)
        if gap_ms and item.get("op") == "text":
            item.setdefault("gap_ms", gap_ms)
        result.append(item)
    return result
