import copy
import json
from pathlib import Path

base = json.loads(Path(__file__).with_name("candidate_raw.json").read_text(encoding="utf-8"))
controls = {}
for name, mutate in (
    ("omit_censored", lambda p: p["rows"].pop(next(i for i, r in enumerate(p["rows"]) if r["censored"]))),
    ("erase_censor", lambda p: p["rows"][next(i for i, r in enumerate(p["rows"]) if r["censored"])].update(censored=False)),
    ("relabel_operator", lambda p: p["rows"][0].update(operator="minimal")),
):
    trial = copy.deepcopy(base)
    mutate(trial)
    # Mutation controls execute the independent predicates inline rather than
    # changing the preserved candidate raw input or calling auditor main.
    seen = {(r.get("initial_state"), r.get("operator")) for r in trial["rows"]}
    if name == "omit_censored":
        rejected = len(trial["rows"]) != 12 or len(seen) != 12
    elif name == "erase_censor":
        rejected = any(r["recurrence_tick"] is None and (r["censored"] is not True or r["censor_horizon"] != 2) for r in trial["rows"])
    else:
        rejected = any(
            r["post_repair_state"] != (0 if r["operator"] == "perfect" else r["pre_repair_state"] if r["operator"] == "minimal" else max(0, r["pre_repair_state"] - 2))
            for r in trial["rows"]
        )
    controls[name] = "REJECTED" if rejected else "ACCEPTED"
print(json.dumps({"mutation_controls": controls}, sort_keys=True))
raise SystemExit(any(value != "REJECTED" for value in controls.values()))
