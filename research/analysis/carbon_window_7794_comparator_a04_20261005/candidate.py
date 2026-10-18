#!/usr/bin/env python3
"""Compare A02 global tuple selection with its stated serial-ASAP baseline."""
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).parent


def feasible(case):
    jobs = [j for j in case["jobs"] if not j["cancelled"]]
    domains = [range(j["release"], min(j["deadline"], j["fresh_until"]) - j["duration"] + 1) for j in jobs]
    rows = []
    for starts in itertools.product(*domains):
        schedule = dict(zip((j["id"] for j in jobs), starts))
        busy = set()
        ok = True
        for job in jobs:
            slots = set(range(schedule[job["id"]], schedule[job["id"]] + job["duration"]))
            if busy & slots or any(schedule[p] + next(x["duration"] for x in jobs if x["id"] == p) > schedule[job["id"]] for p in job["predecessors"]):
                ok = False
                break
            busy |= slots
        if ok:
            rows.append(schedule)
    return jobs, rows


def serial_asap(jobs):
    placed, busy = {}, set()
    for job in jobs:
        earliest = max([job["release"]] + [placed[p] + next(x["duration"] for x in jobs if x["id"] == p) for p in job["predecessors"]])
        found = None
        for start in range(earliest, min(job["deadline"], job["fresh_until"]) - job["duration"] + 1):
            slots = set(range(start, start + job["duration"]))
            if not busy & slots:
                found = start
                busy |= slots
                break
        if found is None:
            return None
        placed[job["id"]] = found
    return placed


def main():
    frozen = json.loads((ROOT / "a02_frozen_cases.json").read_text())
    cases = list(frozen["cases"])
    cases.append({"id":"priority_deadend_discriminator","jobs":[
        {"id":"A","duration":1,"energy_per_slot":1,"release":0,"deadline":3,"fresh_until":3,"predecessors":[],"optional":True,"cancelled":False,"output_sha256":"a"*64},
        {"id":"B","duration":1,"energy_per_slot":1,"release":0,"deadline":1,"fresh_until":1,"predecessors":[],"optional":True,"cancelled":False,"output_sha256":"b"*64}],"forecast":[1,1,1]})
    output = []
    for case in cases:
        jobs, all_rows = feasible(case)
        global_pick = min(all_rows, key=lambda s: tuple(s[j["id"]] for j in jobs)) if all_rows else None
        serial_pick = serial_asap(jobs)
        output.append({"case_id":case["id"],"feasible_count":len(all_rows),"global_lexicographic":global_pick,"serial_asap":serial_pick,"same":global_pick==serial_pick})
    result={"scope":"finite comparator semantics only","input_sha256":hashlib.sha256((ROOT/"a02_frozen_cases.json").read_bytes()).hexdigest(),"rows":output}
    print(json.dumps(result,sort_keys=True,indent=2))


if __name__=="__main__": main()
