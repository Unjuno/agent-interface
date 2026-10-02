"""Exact finite schedule/cue-overlap enumeration for Issue #6067 T0."""
from itertools import product

T = 12
N = 4
MAX_GAP = 18
DURATIONS = (1, 2, 3)


def hits(offset, phase, duration):
    # Integer-slot instantaneous capture; cue interval is half-open modulo T.
    return ((offset - phase) % T) < duration


def admissible(offsets):
    return all(T + offsets[(i + 1) % N] - offsets[i] <= MAX_GAP
               for i in range(N))


def audit_metrics():
    schedules = [s for s in product(range(T), repeat=N) if admissible(s)]
    result = {}
    gap_values = [T + s[(i + 1) % N] - s[i]
                  for s in schedules for i in range(N)]
    for duration in DURATIONS:
        phase_results = []
        for phase in range(T):
            miss = sum(not any(hits(u, phase, duration) for u in s)
                       for s in schedules)
            phase_results.append({"phase": phase, "miss": miss,
                                  "total": len(schedules)})
        periodic_misses = sum(not hits(0, phase, duration)
                              for phase in range(T))
        result[str(duration)] = {
            "miss_numerator_by_phase": [x["miss"] for x in phase_results],
            "admissible_schedule_count": len(schedules),
            "periodic_all_four_miss_phases": periodic_misses,
            "worst_phase_diversified_miss_numerator": max(x["miss"] for x in phase_results),
            "worst_phase_diversified_miss_denominator": len(schedules),
        }
    return {"period": T, "repetitions": N, "max_gap": MAX_GAP,
            "admissible_schedule_count": len(schedules),
            "observed_gap_min": min(gap_values),
            "observed_gap_max": max(gap_values),
            "duration_results": result}


if __name__ == "__main__":
    import json
    print(json.dumps(audit_metrics(), sort_keys=True, indent=2))
