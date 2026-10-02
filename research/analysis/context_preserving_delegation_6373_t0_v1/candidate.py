import copy
import json
import sys

POLICIES = ("NO_RESTORE", "SUMMARY_ONLY", "RESTORE_ONLY", "RESTORE_PLUS_DIFF")


def diff(initial, current):
    return {k: {"before": initial.get(k), "after": current.get(k)}
            for k in sorted(set(initial) | set(current)) if initial.get(k) != current.get(k)}


def run(path):
    fixture = json.load(open(path, encoding="utf-8"))
    rows = []
    for case in fixture["cases"]:
        for policy in POLICIES:
            current = copy.deepcopy(case["terminal"])
            effects = copy.deepcopy(case["effects_after"])
            restored = []
            for field in case["restore_fields"] if policy in ("RESTORE_ONLY", "RESTORE_PLUS_DIFF") else []:
                safe = (policy == "RESTORE_ONLY" or
                        (field not in case["external_fields"] and
                         field not in case["unknown_fields"] and
                         field not in case["restore_side_effects"] and
                         not (field == "download" and current.get(field) in case["required_artifacts"])))
                if safe and field in case["initial"]:
                    current[field] = case["initial"][field]
                    restored.append(field)
                    for effect, value in case["restore_side_effects"].get(field, {}).items():
                        effects[effect] = value
            summary = diff(case["initial"], current) if policy in ("SUMMARY_ONLY", "RESTORE_PLUS_DIFF") else {}
            mismatches = sum(current.get(k) != v for k, v in case["next_requires"].items())
            effects_lost = any(effects.get(k) != v for k, v in case["effects_after"].items())
            artifacts_lost = any(v not in current.values() for v in case["required_artifacts"])
            unresolved_cleared = any(current.get(k) == case["initial"].get(k) for k in case["unknown_fields"] if k in restored)
            rows.append({"case": case["id"], "policy": policy, "context_after": current,
                         "effects_after": effects, "restored_fields": sorted(restored),
                         "residual_state_diff": summary, "modeled_context_mismatches": mismatches,
                         "effects_lost": effects_lost, "external_overwrite": any(k in restored for k in case["external_fields"]),
                         "artifacts_lost": artifacts_lost, "unresolved_cleared": unresolved_cleared})
    return rows


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1]), sort_keys=True, separators=(",", ":")))
