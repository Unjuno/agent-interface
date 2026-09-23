#!/usr/bin/env python3
import itertools, json, pathlib, sys

FIELDS = ["physical_task_effect_endpoint", "task_effect_contract", "matched_arm", "arm_bound_audit", "terminal_integrity"]

def decide(row):
    return "AUTHORIZE" if all(row[k] for k in FIELDS) else "HOLD"

def main(out):
    p = pathlib.Path(out); p.mkdir(parents=True, exist_ok=True)
    vectors = []
    for bits in itertools.product((False, True), repeat=len(FIELDS)):
        row = dict(zip(FIELDS, bits)); row["decision"] = decide(row); vectors.append(row)
    controls = [
        {"name":"missing_receipt", "physical_task_effect_endpoint":True, "task_effect_contract":True, "matched_arm":True, "arm_bound_audit":True, "terminal_integrity":False},
        {"name":"stale_binding", "physical_task_effect_endpoint":True, "task_effect_contract":True, "matched_arm":False, "arm_bound_audit":True, "terminal_integrity":True},
        {"name":"unknown_boundary", "physical_task_effect_endpoint":False, "task_effect_contract":True, "matched_arm":True, "arm_bound_audit":True, "terminal_integrity":True},
        {"name":"cleanup_failure", "physical_task_effect_endpoint":True, "task_effect_contract":True, "matched_arm":True, "arm_bound_audit":True, "terminal_integrity":False},
        {"name":"corrupt_recomputation", "physical_task_effect_endpoint":True, "task_effect_contract":True, "matched_arm":True, "arm_bound_audit":False, "terminal_integrity":True},
    ]
    for row in controls: row["decision"] = decide(row)
    data = {"schema":"map01-recovery-entry-gate-3008-v2", "fields":FIELDS, "vectors":vectors, "controls":controls}
    (p/"raw.json").write_text(json.dumps(data, indent=2, sort_keys=True)+"\n")
    print(f"RAW vectors={len(vectors)} controls={len(controls)}")

if __name__ == "__main__": main(sys.argv[1])
