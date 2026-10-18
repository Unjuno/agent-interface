"""Deterministic new T0 workload generator; no random or host inputs."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).parent
OUT = Path(os.environ.get("OUTPUT_DIR", ROOT))
H = 24


def job(job_id, cls, release, execution, deadline, preemptible=True):
    return {"id": job_id, "class": cls, "release": release,
            "execution": execution, "deadline": deadline,
            "preemptible": preemptible}


def trace(name, controls, soft, contract, kind="eligible"):
    return {"trace_id": name, "horizon": H, "kind": kind,
            "contract": contract, "jobs": controls + soft}


def workloads():
    c = lambda gap, wcet, rel_deadline, total=None: {
        "min_interarrival": gap, "max_execution": wcet,
        "relative_deadline": rel_deadline, "preemptive": True,
        **({"max_jobs_total": total} if total is not None else {})}
    return [
        trace("idle_gaps",
              [job("c0", "control", 1, 1, 5), job("c1", "control", 7, 1, 11),
               job("c2", "control", 13, 1, 17)],
              [job("s0", "soft", 0, 15, H), job("s1", "soft", 5, 10, H)],
              c(5, 1, 4)),
        trace("idle_gaps_dense_soft",
              [job("c0", "control", 2, 1, 6), job("c1", "control", 10, 1, 14)],
              [job("s0", "soft", 0, 22, H)],
              c(6, 1, 4)),
        trace("replenishment_boundary",
              [job("c0", "control", 7, 1, 11), job("c1", "control", 13, 1, 17)],
              [job("s0", "soft", 0, 22, H)],
              c(5, 1, 4)),
        trace("exact_demand_boundary",
              [job("c0", "control", 0, 2, 2), job("c1", "control", 4, 2, 6)],
              [job("s0", "soft", 0, 8, H)],
              c(4, 2, 2)),
        trace("burst_at_replenishment",
              [job("c0", "control", 7, 1, 11), job("c1", "control", 8, 1, 12),
               job("c2", "control", 9, 1, 13)],
              [job("s0", "soft", 0, 22, H)],
              c(1, 1, 4, 3)),
        trace("infeasible_joint_demand",
              [job("c0", "control", 0, 2, 2), job("c1", "control", 1, 2, 3)],
              [job("s0", "soft", 0, 4, H)],
              c(1, 2, 2), "infeasible"),
        trace("unknown_wcet",
              [{"id": "c0", "class": "control", "release": 0,
                "execution": None, "deadline": 4, "preemptible": True}],
              [job("s0", "soft", 0, 3, H)],
              c(4, 1, 4), "unknown"),
        trace("unknown_nonpreemptive",
              [job("c0", "control", 0, 1, 4, False)],
              [job("s0", "soft", 0, 3, H)],
              {"min_interarrival": 4, "max_execution": 1,
               "relative_deadline": 4, "preemptive": False}, "unknown"),
        trace("invalid_job_class",
              [job("c0", "controller", 0, 1, 4)],
              [job("s0", "soft", 0, 3, H)],
              c(4, 1, 4), "invalid"),
    ]


def main():
    (OUT / "inputs.json").write_text(
        json.dumps({"allocation": "UNJUNO-7778-SLACK-RECLAMATION-T0-20261005-01",
                    "traces": workloads()}, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8")


if __name__ == "__main__":
    main()
