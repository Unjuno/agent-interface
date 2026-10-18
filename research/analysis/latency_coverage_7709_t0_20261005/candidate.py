#!/usr/bin/env python3
"""Frozen candidate: naive attempt-i.i.d. vs segment-report/session inference."""
import json
import math
import statistics
import sys

Z975 = 1.959963984540054


def critical(df):
    if df == 7:
        return 2.364624251
    if df == 15:
        return 2.131449546
    z = Z975
    return z + (z**3 + z) / (4 * df) + (5*z**5 + 16*z**3 + 3*z) / (96 * df**2)


def interval(values):
    mean = statistics.fmean(values)
    sd = statistics.stdev(values)
    half = critical(len(values) - 1) * sd / math.sqrt(len(values))
    return [mean, mean - half, mean + half]


def segment_edges(sessions, threshold, minimum, max_count):
    tcount = len(sessions[0])
    signal = [statistics.fmean((s[t][0] + s[t][1]) / 2.0 for s in sessions) for t in range(tcount)]
    edges = []

    def split(lo, hi):
        if len(edges) >= max_count - 1 or hi - lo < 2 * minimum:
            return
        best_t, best_gap = None, -1.0
        for cut in range(lo + minimum, hi - minimum + 1):
            left = statistics.fmean(signal[lo:cut])
            right = statistics.fmean(signal[cut:hi])
            gap = abs(right - left)
            if gap > best_gap:
                best_t, best_gap = cut, gap
        if best_t is not None and best_gap >= threshold:
            edges.append(best_t)
            split(lo, best_t)
            split(best_t, hi)

    split(0, tcount)
    return sorted(edges)


def integrated_per_session(sessions, edges):
    bounds = [0] + list(edges) + [len(sessions[0])]
    out = []
    for session in sessions:
        weighted = 0.0
        for left, right in zip(bounds, bounds[1:]):
            d = statistics.fmean(session[t][1] - session[t][0] for t in range(left, right))
            weighted += (right - left) * d
        out.append(weighted / bounds[-1])
    return out


def summarize(row, cfg):
    sessions = row["sessions"]
    flat = [b - a for session in sessions for a, b, _ in session]
    edges = segment_edges(sessions, cfg["segment_split_threshold_ms"], cfg["segment_min_windows"], cfg["segment_max_count"])
    aware_values = integrated_per_session(sessions, edges)
    base = interval(flat)
    aware = interval(aware_values)
    no_edges = interval(integrated_per_session(sessions, []))
    tcount = len(sessions[0])
    extra = list(range(cfg["segment_min_windows"], tcount, cfg["segment_min_windows"]))
    extra = [x for x in extra if min(x, tcount - x) >= cfg["segment_min_windows"]]
    extra_interval = interval(integrated_per_session(sessions, extra))
    censored = sum(c for session in sessions for _, _, c in session)
    bounds = [0] + edges + [len(sessions[0])]
    strata = []
    for left, right in zip(bounds, bounds[1:]):
        values = [session[t][1] - session[t][0] for session in sessions for t in range(left, right)]
        strata.append({
            "start": left, "end": right, "paired_windows": len(values),
            "censored_windows": sum(session[t][2] for session in sessions for t in range(left, right)),
            "mean_delta_ms": statistics.fmean(values),
        })
    return {
        "case": row["case"], "n": row["n"], "rep": row["rep"], "truth_ms": row["truth_ms"],
        "window_rows": len(flat), "censored_rows": censored, "edges": edges, "segments": strata,
        "base": base, "aware": aware,
        "no_boundary_max_error": max(abs(x-y) for x, y in zip(aware, no_edges)),
        "extra_boundary_max_error": max(abs(x-y) for x, y in zip(aware, extra_interval)),
    }


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as source, open(sys.argv[2], "w", encoding="utf-8", newline="\n") as dest:
        cfg = json.load(open(sys.argv[3], encoding="utf-8"))
        for line in source:
            result = summarize(json.loads(line), cfg)
            dest.write(json.dumps(result, separators=(",", ":"), sort_keys=True) + "\n")
