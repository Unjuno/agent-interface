"""Build the frozen, fixed-seed workload matrix for Issue #7778 T0."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build_cases():
    cases = []
    # Four distinct release shapes, four fixed seeds each.  The late-release
    # profile is the preregistered positive-slack subset: both reserved periods
    # 0 and 1 have no possible control release while soft work is ready.
    profiles = {
        "late_single": [([16, 17, 18], "s0", 6)],
        "early_single": [([6, 7, 8, 9], "s0", 6)],
        "boundary_burst_pair": [([7, 8, 9], "s0", 4), ([7, 8, 9], "s1", 4)],
        "late_separated_three": [
            ([16, 17, 18], "s0", 6),
            ([16, 17, 18], "s1", 6),
            ([24, 25, 26], "s0", 6),
        ],
    }
    for profile, specs in profiles.items():
        for replicate in range(4):
            seed = 777800 + len(cases)
            rng = random.Random(seed)
            controls = []
            chosen_by_stream = {}
            for index, (choices, stream, minimum_gap) in enumerate(specs):
                legal = [
                    value for value in choices
                    if all(abs(value - prior) >= minimum_gap
                           for prior in chosen_by_stream.get(stream, []))
                ]
                if not legal:
                    raise AssertionError(f"no legal release for {profile}/{index}")
                release = rng.choice(legal)
                chosen_by_stream.setdefault(stream, []).append(release)
                wcet = 1 if profile == "boundary_burst_pair" else rng.choice([1, 2])
                if profile == "boundary_burst_pair":
                    relative_deadline = 1
                else:
                    max_deadline = min(8, 32 - max(choices))
                    relative_deadline = rng.choice([d for d in [4, 5, 6, 8] if d <= max_deadline])
                controls.append({
                    "id": f"c{index}", "class": "control", "stream": stream,
                    "release_choices": choices, "actual_release": release,
                    "min_interarrival": minimum_gap, "wcet": wcet,
                    "relative_deadline": relative_deadline, "preemptible": True,
                })
            # Each profile has two different-size best-effort jobs.  The jobs
            # are released at zero and have a common finite horizon, not hard
            # deadlines; only their completed CPU work is scored.
            soft = [
                {"id": "b0", "class": "best_effort", "release": 0,
                 "wcet": 12, "preemptible": True},
                {"id": "b1", "class": "best_effort", "release": 0,
                 "wcet": 16, "preemptible": True},
            ]
            controls_sorted = sorted(controls, key=lambda item: item["id"])
            positive = profile in {"late_single", "late_separated_three"}
            cases.append({
                "case_id": f"{profile}-{replicate + 1:02d}",
                "seed": seed,
                "profile": profile,
                "horizon": 32,
                "min_interarrival_contract": "same-stream releases separated by the job's frozen minimum_interarrival",
                "controls": controls_sorted,
                "soft_jobs": soft,
                "positive_slack_subset": positive,
            })
    for case_id, deadline in (("exact-boundary", 2), ("joint-infeasible", 1)):
        controls = [
            {"id": "c0", "class": "control", "stream": "s0",
             "release_choices": [8], "actual_release": 8,
             "min_interarrival": 1, "wcet": 1,
             "relative_deadline": deadline, "preemptible": True},
            {"id": "c1", "class": "control", "stream": "s1",
             "release_choices": [8], "actual_release": 8,
             "min_interarrival": 1, "wcet": 1,
             "relative_deadline": deadline, "preemptible": True},
        ]
        cases.append({
            "case_id": case_id, "seed": 777899 if deadline == 2 else 777898,
            "profile": case_id, "horizon": 32,
            "min_interarrival_contract": "same-stream releases separated by the job's frozen minimum_interarrival",
            "controls": controls,
            "soft_jobs": [
                {"id": "b0", "class": "best_effort", "release": 0,
                 "wcet": 12, "preemptible": True},
                {"id": "b1", "class": "best_effort", "release": 0,
                 "wcet": 16, "preemptible": True},
            ],
            "positive_slack_subset": False,
        })
    return {
        "schema": "7778-slack-reclamation-cases-v1",
        "model": {
            "processor_count": 1, "service_per_tick": 1,
            "tick_semantics": "one unit of CPU service occupies [t,t+1)",
            "period": 8, "static_control_budget": 2,
            "static_best_effort_budget": 6,
            "overhead_sensitivity_units_per_job_dispatch": [0, 1],
            "soft_deadline": "horizon only; no soft deadline guarantee",
        },
        "policy_definitions": {
            "PRIORITY_ONLY": "preemptive EDF among released controls; otherwise FIFO best-effort; no reserved quota",
            "STATIC_RESERVATION": "each 8-tick period grants at most 2 control service ticks and 6 best-effort service ticks; unused control budget expires and cannot be borrowed",
            "DEMAND_GUARDED_SLACK_STEAL": "EDF control service; a best-effort tick is admitted only if exhaustive future release choices in the frozen finite envelope remain control-feasible",
        },
        "cases": cases,
        "refusal_controls": [
            {"id": "unknown-wcet", "job": {"id": "c0", "class": "control", "wcet": None, "preemptible": True}, "expected": "HOLD_UNKNOWN_WCET"},
            {"id": "nonpreemptible", "job": {"id": "c0", "class": "control", "wcet": 1, "preemptible": False}, "expected": "UNKNOWN_MODEL_MISMATCH"},
            {"id": "invalid-job-class", "job": {"id": "c0", "class": "unrecognized", "wcet": 1, "preemptible": True}, "expected": "REJECT_INVALID_JOB_CLASS"},
        ],
    }


if __name__ == "__main__":
    (ROOT / "cases.json").write_text(
        json.dumps(build_cases(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
