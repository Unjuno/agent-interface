#!/usr/bin/env python3
"""Candidate for Issue #7409 A02: revision-token evidence in the draft gate."""
import json
import re
import sys


REVISION = re.compile(r"r(?:0|[1-9][0-9]*)\Z")


def valid_revision(value):
    return isinstance(value, str) and REVISION.fullmatch(value) is not None


def next_revision(value):
    return f"r{int(value[1:]) + 1}" if valid_revision(value) else None


def patch(document, values):
    result = dict(document)
    result.update(values)
    return result


def run_case(case):
    base = dict(case["base"])
    base_revision = case["base_revision"]
    current_revision = case["human"]["revision_after_commit"]
    human_live = patch(base, case["human"]["writes"])
    direct = {
        "status": "DIRECT_COMMITTED",
        "final": patch(human_live, case["agent"]["writes"]),
        "revision": next_revision(current_revision),
        "external_effects": list(case["agent"]["external_effects"]),
    }

    app = case["app"]
    eligible = (
        app["versioned_draft"]
        and app["draft_backend_isolated"]
        and app["no_external_effects"]
        and not case["agent"]["external_effects"]
    )
    if not eligible:
        reason = "SHARED_BACKEND" if not app["draft_backend_isolated"] else "EXTERNAL_EFFECT"
        staged = {
            "status": "REFUSED_ELIGIBILITY", "reason": reason, "draft_created": False, "draft": None,
            "live_after_draft_write": human_live, "final": human_live, "final_revision": current_revision,
            "revision_observation": None, "conflicts": [], "promoted": False, "external_effects": [],
            "events": ["HUMAN_COMMIT", "REFUSED_BEFORE_DRAFT"],
        }
        return {"case_id": case["id"], "direct": direct, "staged": staged}

    draft = patch(base, case["agent"]["writes"])
    live_after_draft_write = dict(base)
    live_after_human_commit = patch(live_after_draft_write, case["human"]["writes"])
    events = ["DRAFT_CREATED", "DRAFT_WRITE_PRIVATE", "HUMAN_COMMIT", "READ_BASE_REVISION", "READ_LIVE_REVISION", "REVISION_COMPARE"]
    base_valid = valid_revision(base_revision)
    live_valid = valid_revision(current_revision)
    observation = {
        "base_revision": base_revision,
        "live_revision": current_revision,
        "base_token_valid": base_valid,
        "live_token_valid": live_valid,
        "tokens_equal": base_revision == current_revision if base_valid and live_valid else None,
        "gate": "UNKNOWN" if not (base_valid and live_valid) else ("MATCH" if base_revision == current_revision else "CHANGED"),
        "event_index": len(events) - 1,
    }
    touched = set(case["agent"]["writes"]) | set(case["agent"]["reads"])
    conflicts = sorted(touched.intersection(case["human"]["writes"]))
    events.append("CHECK_READ_WRITE_CONFLICTS")

    if not (base_valid and live_valid):
        status, reason, final, final_revision, promoted = "HOLD_REVISION_UNKNOWN", "INVALID_OR_MISSING_REVISION_TOKEN", live_after_human_commit, current_revision, False
        events.append("PROMOTION_HELD_UNKNOWN_REVISION")
    elif conflicts:
        status, reason, final, final_revision, promoted = "CONFLICT_HOLD", "OVERLAPPING_READ_OR_WRITE", live_after_human_commit, current_revision, False
        events.append("CONFLICT_SURFACED")
    elif not app["explicit_promotion"]:
        status, reason, final, final_revision, promoted = "HOLD_PROMOTION_NOT_AUTHORIZED", "NO_EXPLICIT_PROMOTION", live_after_human_commit, current_revision, False
        events.append("PROMOTION_HELD")
    else:
        status, reason = "PROMOTED", "REVISION_GATE_AND_CONFLICT_CHECK_PASSED"
        final = patch(live_after_human_commit, case["agent"]["writes"])
        final_revision, promoted = next_revision(current_revision), True
        events.append("EXPLICIT_PROMOTION")

    promotion_index = events.index("EXPLICIT_PROMOTION") if promoted else None
    observation["promotion_event_index"] = promotion_index
    staged = {
        "status": status, "reason": reason, "draft_created": True, "draft": draft,
        "live_after_draft_write": live_after_draft_write,
        "live_after_human_commit": live_after_human_commit,
        "final": final, "final_revision": final_revision,
        "revision_observation": observation,
        "conflicts": conflicts, "promoted": promoted, "external_effects": [], "events": events,
    }
    return {"case_id": case["id"], "direct": direct, "staged": staged}


def main():
    source, destination = sys.argv[1:3]
    with open(source, encoding="utf-8") as stream:
        cases = json.load(stream)
    result = {"schema": "issue-7409-t0-a02-candidate-v1", "rows": [run_case(case) for case in cases]}
    with open(destination, "w", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps({"schema": result["schema"], "row_count": len(result["rows"]), "output": destination}, sort_keys=True))


if __name__ == "__main__":
    main()
