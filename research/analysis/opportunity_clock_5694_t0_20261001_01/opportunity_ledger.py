"""Finite event simulation for Issue #5694; no external side effects."""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Opportunity:
    opportunity_id: str
    onset_ms: int
    expiry_ms: int


def percentile95(values: list[int]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(0.95 * len(ordered)) - 1]


def simulate(name: str, opportunities: list[Opportunity], latency_ms: int,
             busy_intervals: list[tuple[int, int]], safe_stop_ids: set[str] | None = None,
             clock_aligned: bool = True) -> dict:
    safe_stop_ids = safe_stop_ids or set()
    cycles = []
    for opportunity in opportunities:
        if not clock_aligned:
            outcome, start_ms, end_ms = "unknown_clock", None, None
        elif any(start < opportunity.expiry_ms and end > opportunity.onset_ms
                 and opportunity.onset_ms >= start and opportunity.onset_ms < end
                 for start, end in busy_intervals):
            outcome, start_ms, end_ms = "miss_expired", None, None
        else:
            start_ms = max(opportunity.onset_ms,
                           max((end for start, end in busy_intervals
                                if start <= opportunity.onset_ms < end), default=opportunity.onset_ms))
            end_ms = start_ms + latency_ms
            if start_ms > opportunity.expiry_ms or end_ms > opportunity.expiry_ms:
                outcome = "miss_expired"
            elif opportunity.opportunity_id in safe_stop_ids:
                outcome = "safe_stop"
            else:
                outcome = "useful_effect"
        cycles.append({"opportunity_id": opportunity.opportunity_id,
                       "onset_ms": opportunity.onset_ms, "expiry_ms": opportunity.expiry_ms,
                       "clock_aligned": clock_aligned, "decision_start_ms": start_ms,
                       "effect_end_ms": end_ms, "outcome": outcome})
    measured = [x["effect_end_ms"] - x["decision_start_ms"] for x in cycles
                if x["outcome"] in {"useful_effect", "safe_stop"}]
    return {"controller": name, "busy_intervals": [list(x) for x in busy_intervals],
            "declared_cycle_latency_ms": latency_ms, "opportunities": cycles,
            "summary": {"opportunity_count": len(cycles),
                        "useful_effect_count": sum(x["outcome"] == "useful_effect" for x in cycles),
                        "safe_stop_count": sum(x["outcome"] == "safe_stop" for x in cycles),
                        "miss_expired_count": sum(x["outcome"] == "miss_expired" for x in cycles),
                        "unknown_clock_count": sum(x["outcome"] == "unknown_clock" for x in cycles),
                        "completed_cycle_p95_ms": percentile95(measured),
                        "useful_opportunity_coverage": sum(x["outcome"] == "useful_effect" for x in cycles) / len(cycles) if cycles else None,
                        "handled_opportunity_fraction": sum(x["outcome"] in {"useful_effect", "safe_stop"} for x in cycles) / len(cycles) if cycles else None}}


def build_raw() -> dict:
    schedule = [Opportunity(f"opp-{i:02d}", i * 100, i * 100 + 90) for i in range(12)]
    overlap = [Opportunity("overlap-a", 0, 100), Opportunity("overlap-b", 50, 140)]
    return {
        "schema": "issue5694-opportunity-clock-raw-v1",
        "clock_domain": "simulated_monotonic_ms-v1",
        "schedule": [asdict(x) for x in schedule],
        "scenarios": {
            "no_stall_fast": simulate("no_stall_fast", schedule, 20, []),
            "true_useful_fast": simulate("true_useful_fast", schedule, 35, []),
            "sparse_fast_with_busy_periods": simulate("sparse_fast_with_busy_periods", schedule, 10, [(100, 500), (700, 1000)]),
            "safe_stop_control": simulate("safe_stop_control", schedule[:3], 20, [], {"opp-01"}),
            "expiry_control": simulate("expiry_control", [Opportunity("expired", 0, 30)], 35, []),
            "overlap_control": simulate("overlap_control", overlap, 20, []),
            "unsynchronized_clock_control": simulate("unsynchronized_clock_control", schedule[:2], 10, [], clock_aligned=False),
        },
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("refuse to overwrite output")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(build_raw(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()

