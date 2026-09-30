"""Independent raw-only auditor for #5352. Deliberately imports no simulator code."""
import hashlib
import json
from itertools import product

ALPHABET = "0123456789ABCDEFGHIJ"
NAMES = ("raw", "fixed_hysteresis", "minimum_dwell")
RISK_LEVEL_COUNT = 5
HIGH = 3
LOW = 1
DWELL = 2


def expected_traces():
    for length in (1, 2, 3):
        yield from product(range(20), repeat=length)


def candidate_modes(trace):
    # Independent reconstruction; integer flags decoded directly from the symbol.
    outputs = {name: [] for name in NAMES}
    for name in NAMES:
        state = 0
        wait = 0
        for symbol in trace:
            risk = symbol % RISK_LEVEL_COUNT
            stale = bool((symbol // RISK_LEVEL_COUNT) % 2)
            critical = symbol // 10 == 1
            if name == "raw":
                state = int(stale or critical or risk >= HIGH)
            elif stale:
                state, wait = 0, 0
                outputs[name].append(1)
                continue
            elif critical:
                state = 1
                if name == "minimum_dwell":
                    wait = DWELL
            elif name == "fixed_hysteresis":
                if state == 0 and risk >= HIGH:
                    state = 1
                elif state == 1 and risk <= LOW:
                    state = 0
            else:
                if state == 0 and risk >= HIGH:
                    state, wait = 1, DWELL
                elif state == 1:
                    if wait:
                        wait -= 1
                    elif risk < HIGH:
                        state = 0
            outputs[name].append(state)
    return outputs


def expected_line(trace):
    decisions = candidate_modes(trace)
    encoded = "".join(ALPHABET[s] for s in trace)
    return (encoded + "|" + "|".join(
        "".join(str(v) for v in decisions[name]) for name in NAMES)).encode("ascii")


def switches(bits):
    return sum(left != right for left, right in zip(bits, bits[1:]))


def is_boundary(trace):
    risks = set()
    for symbol in trace:
        if symbol >= 10 or (symbol // 5) % 2:
            return False
        risks.add(symbol % 5)
    return risks == {2, 3}


def is_fresh_noncritical(trace):
    return all(symbol < 10 and (symbol // 5) % 2 == 0 for symbol in trace)


def is_monotone_deterioration(trace):
    if not is_fresh_noncritical(trace):
        return False
    risks = [symbol % 5 for symbol in trace]
    return all(a <= b for a, b in zip(risks, risks[1:])) and any(r >= HIGH for r in risks)


def summarize(rows):
    totals = {name: 0 for name in NAMES}
    boundary = {name: 0 for name in NAMES}
    critical_count = stale_count = 0
    critical_miss = {name: 0 for name in NAMES}
    stale_miss = {name: 0 for name in NAMES}
    monotone_count = 0
    max_delay = {name: 0 for name in NAMES}
    final_mismatch = {name: 0 for name in NAMES}
    boundary_count = 0
    for trace, modes in rows:
        for name in NAMES:
            totals[name] += switches(modes[name])
        if is_boundary(trace):
            boundary_count += 1
            for name in NAMES:
                boundary[name] += switches(modes[name])
        if is_fresh_noncritical(trace):
            for name in NAMES[1:]:
                final_mismatch[name] += modes[name][-1] != modes["raw"][-1]
        for i, symbol in enumerate(trace):
            stale = bool((symbol // 5) % 2)
            critical = symbol // 10 == 1
            critical_count += critical
            stale_count += stale
            for name in NAMES:
                critical_miss[name] += critical and modes[name][i] != 1
                stale_miss[name] += stale and modes[name][i] != 1
        if is_monotone_deterioration(trace):
            monotone_count += 1
            first_high = next(i for i, s in enumerate(trace) if s % 5 >= HIGH)
            for name in NAMES:
                first_escalated = next((i for i, v in enumerate(modes[name]) if v == 1), len(trace))
                max_delay[name] = max(max_delay[name], first_escalated - first_high)
    reduced = {name: boundary[name] < boundary["raw"] for name in NAMES[1:]}
    gates = {
        "boundary_switch_reduction": reduced,
        "critical_same_row": {name: critical_miss[name] == 0 for name in NAMES},
        "stale_same_row": {name: stale_miss[name] == 0 for name in NAMES},
        "monotone_no_extra_delay": {name: max_delay[name] == 0 for name in NAMES},
        "final_mode_matches_raw_noncritical": {name: final_mismatch[name] == 0 for name in NAMES[1:]},
    }
    passed = all(all(v.values()) for v in gates.values())
    return {
        "trace_count": len(rows),
        "switches_all_traces": totals,
        "boundary_trace_count": boundary_count,
        "boundary_switches": boundary,
        "critical_observation_count": critical_count,
        "stale_observation_count": stale_count,
        "critical_misses": critical_miss,
        "stale_misses": stale_miss,
        "monotone_deterioration_trace_count": monotone_count,
        "max_crossing_delay_observations": max_delay,
        "final_mode_mismatches_noncritical": final_mismatch,
        "gates": gates,
        "disposition": "PASS_HYSTERESIS_T0_SCOPED" if passed else "FAIL_SAFETY_OR_REFERENCE_GATE",
    }


def verify(raw):
    errors = []
    lines = raw.splitlines()
    rows = []
    for index, trace in enumerate(expected_traces()):
        if index >= len(lines):
            errors.append("missing_row")
            break
        expected = expected_line(trace)
        if lines[index] != expected:
            errors.append(f"row_mismatch_{index}")
        rows.append((trace, candidate_modes(trace)))
    expected_count = 20 + 400 + 8000
    if len(lines) != expected_count:
        errors.append("row_count")
    digest = hashlib.sha256(raw).hexdigest()
    summary = summarize(rows)
    return {"audit_pass": not errors, "errors": errors[:20], "raw_sha256": digest, **summary}


def main():
    import sys
    raw = sys.stdin.buffer.read()
    result = verify(raw)
    if not result["audit_pass"]:
        print(json.dumps(result, sort_keys=True))
        raise SystemExit(1)
    first = raw.splitlines()[0]
    fields = first.split(b"|")
    mutations = {}
    changed = list(fields)
    flip = bytearray(changed[1])
    flip[0] = ord("1") if flip[0] == ord("0") else ord("0")
    changed[1] = bytes(flip)
    mutations["decision_bit_flip_rejected"] = not verify(b"|".join(changed) + b"\n" + b"\n".join(raw.splitlines()[1:]))["audit_pass"]
    lines = raw.splitlines()
    bad = lines.copy()
    bad[0] = b"K" + bad[0][1:]
    mutations["invalid_symbol_rejected"] = not verify(b"\n".join(bad) + b"\n")["audit_pass"]
    mutations["duplicate_row_rejected"] = not verify(raw + lines[0] + b"\n")["audit_pass"]
    result["mutation_controls"] = mutations
    result["audit_pass"] = all(mutations.values())
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["audit_pass"] else 1)


if __name__ == "__main__":
    main()
