"""Strict job-class candidate for the #7748 finite-demand audit boundary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


KNOWN_CLASSES = frozenset({"control", "best_effort"})
JOB_FIELDS = ("id", "class", "release", "execution", "deadline", "preemptible")


def _edf_feasible(jobs: list[dict]) -> bool:
    if not jobs:
        return True
    pending = {job["id"]: job["execution"] for job in jobs}
    end = max(job["deadline"] for job in jobs)
    for now in range(min(job["release"] for job in jobs), end):
        ready = [
            job for job in jobs
            if job["release"] <= now and pending[job["id"]] > 0
        ]
        if ready:
            selected = min(ready, key=lambda job: (job["deadline"], job["id"]))
            pending[selected["id"]] -= 1
        if any(
            job["deadline"] == now + 1 and pending[job["id"]] > 0
            for job in jobs
        ):
            return False
    return not any(pending.values())


def classify(case: dict) -> dict:
    jobs = case.get("jobs") if isinstance(case, dict) else None
    if not isinstance(jobs, list) or not jobs:
        return {"status": "HOLD_NO_SCHEDULABILITY_INPUTS"}

    for job in jobs:
        if not isinstance(job, dict):
            return {"status": "HOLD_NO_SCHEDULABILITY_INPUTS"}
        if "class" not in job or type(job["class"]) is not str or job["class"] not in KNOWN_CLASSES:
            return {"status": "HOLD_UNKNOWN_JOB_CLASS"}
        if any(field not in job for field in JOB_FIELDS):
            return {"status": "HOLD_NO_SCHEDULABILITY_INPUTS"}
        if job["preemptible"] is not True:
            return {"status": "UNKNOWN_MODEL_MISMATCH"}
        if (
            type(job["release"]) is not int
            or type(job["execution"]) is not int
            or type(job["deadline"]) is not int
            or job["release"] < 0
            or job["execution"] <= 0
            or job["deadline"] <= job["release"]
            or type(job["id"]) is not str
            or not job["id"]
        ):
            return {"status": "HOLD_NO_SCHEDULABILITY_INPUTS"}

    identifiers = [job["id"] for job in jobs]
    if len(set(identifiers)) != len(identifiers):
        return {"status": "HOLD_DUPLICATE_JOB_ID"}

    controls = [job for job in jobs if job["class"] == "control"]
    return {
        "status": "ELIGIBLE",
        "control_feasible": _edf_feasible(controls),
        "all_feasible": _edf_feasible(jobs),
    }


def run(cases: list[dict]) -> dict:
    return {
        "schema": "7748-duplicate-id-a02-raw-v1",
        "rows": [
            {"input": case, "result": classify(case)}
            for case in cases
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    cases_path = Path(__file__).with_name("cases.json")
    cases = json.loads(cases_path.read_text(encoding="utf-8"))["cases"]
    raw = run(cases)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"schema": raw["schema"], "rows": len(raw["rows"]), "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
