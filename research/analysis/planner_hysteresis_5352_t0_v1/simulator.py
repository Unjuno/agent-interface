"""Frozen candidate state machines for Issue #5352; pure Python, no runtime hooks."""
from itertools import product

RISK_LEVELS = (0.0, 0.3, 0.5, 0.7, 1.0)
HIGH_INDEX = 3
LOW_INDEX = 1
MIN_DWELL = 2
POLICIES = ("raw", "fixed_hysteresis", "minimum_dwell")
ALPHABET = "0123456789ABCDEFGHIJ"


def decode_symbol(code):
    if type(code) is not int or not 0 <= code < 20:
        raise ValueError("symbol must be an integer in 0..19")
    return code % 5, bool((code // 5) % 2), bool(code >= 10)


def run_policy(trace, policy):
    if policy not in POLICIES:
        raise ValueError("unknown policy")
    mode = 0
    remaining = 0
    result = []
    for symbol in trace:
        risk, stale, critical = decode_symbol(symbol)
        if policy == "raw":
            mode = int(stale or critical or risk >= HIGH_INDEX)
        elif stale:
            # Emit a hard override now; stale state cannot carry forward.
            mode, remaining = 0, 0
            result.append(1)
            continue
        elif critical:
            mode = 1
            if policy == "minimum_dwell":
                remaining = MIN_DWELL
        elif policy == "fixed_hysteresis":
            if mode == 0 and risk >= HIGH_INDEX:
                mode = 1
            elif mode == 1 and risk <= LOW_INDEX:
                mode = 0
        else:  # minimum_dwell
            if mode == 0 and risk >= HIGH_INDEX:
                mode, remaining = 1, MIN_DWELL
            elif mode == 1:
                if remaining > 0:
                    remaining -= 1
                elif risk < HIGH_INDEX:
                    mode = 0
        result.append(mode)
    return tuple(result)


def traces(max_length=3):
    for length in range(1, max_length + 1):
        yield from product(range(20), repeat=length)


def encode_trace(trace):
    return "".join(ALPHABET[symbol] for symbol in trace)


def render_raw():
    for trace in traces():
        modes = [run_policy(trace, policy) for policy in POLICIES]
        yield (encode_trace(trace) + "|" +
               "|".join("".join(str(bit) for bit in mode) for mode in modes) +
               "\n").encode("ascii")


if __name__ == "__main__":
    import sys
    out = sys.stdout.buffer
    for record in render_raw():
        out.write(record)
