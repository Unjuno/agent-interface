"""Research tail compatibility wrapper for shared bounded key expansion."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from runtime.core_v1.sequence import expand_key_repeats


def expand_tail(tail, *, max_ops):
    if type(max_ops) is not int or not 0 <= max_ops <= 126:
        raise ValueError('native tail capacity must be 0..126')
    return expand_key_repeats(tail, max_ops=max_ops)
