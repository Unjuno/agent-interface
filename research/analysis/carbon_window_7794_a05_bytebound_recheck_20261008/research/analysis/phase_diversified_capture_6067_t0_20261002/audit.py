"""Independent exact audit. Uses integer-coded schedules, no candidate imports."""
from itertools import product


def independently_audit():
    period, cycles, gap_cap = 12, 4, 18
    widths = (1, 2, 3)
    schedule_total = 0
    rows = {w: [] for w in widths}
    # Decode each integer as a base-12 offset tuple, independently of candidate.
    for code in range(period ** cycles):
        x = code
        seq = [0] * cycles
        for j in range(cycles - 1, -1, -1):
            seq[j] = x % period
            x //= period
        valid = True
        for j in range(cycles):
            nxt = seq[(j + 1) % cycles]
            if period + nxt - seq[j] > gap_cap:
                valid = False
                break
        if not valid:
            continue
        schedule_total += 1
        for width in widths:
            for phase in range(period):
                seen = False
                for offset in seq:
                    distance = (offset - phase) % period
                    if distance < width:
                        seen = True
                        break
                if not seen:
                    rows[width].append(phase)
    output = {}
    for width in widths:
        counts = [rows[width].count(p) for p in range(period)]
        periodic = sum(1 for phase in range(period)
                       if (0 - phase) % period >= width)
        output[str(width)] = {
            "miss_count_by_phase": counts,
            "schedule_count": schedule_total,
            "periodic_miss_phase_count": periodic,
            "worst_phase_miss_count": max(counts),
        }
    return {"schedule_count": schedule_total, "results": output}


if __name__ == "__main__":
    import json
    print(json.dumps(independently_audit(), sort_keys=True, indent=2))
