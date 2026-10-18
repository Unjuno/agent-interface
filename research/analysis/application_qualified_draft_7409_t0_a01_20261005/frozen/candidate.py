#!/usr/bin/env python3
"""One-shot candidate for the synthetic Issue #7409 T0 fixture."""
import json
import sys


def apply_patch(document, patch):
    result = dict(document)
    result.update(patch)
    return result


def next_revision(revision):
    return f"r{int(revision[1:]) + 1}"


def run_case(case):
    base = dict(case["base"])
    human_live = apply_patch(base, case["human"]["writes"])
    live_revision = case["human"].get("revision_after_commit", "r1")

    # Comparator: direct editing writes into the common live artifact.
    direct_live = apply_patch(human_live, case["agent"]["writes"])
    direct = {
        "final": direct_live,
        "revision": next_revision(live_revision),
        "agent_writes_reached_live_before_completion": bool(case["agent"]["writes"]),
        "external_effects": list(case["agent"]["external_effects"]),
        "status": "DIRECT_COMMITTED",
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
        return {
            "case_id": case["id"],
            "direct": direct,
            "staged": {
                "status": "REFUSED_ELIGIBILITY",
                "reason": reason,
                "draft_created": False,
                "draft": None,
                "live_after_draft_write": human_live,
                "live_revision_after_draft_write": live_revision,
                "live_after_human_commit": human_live,
                "final": human_live,
                "final_revision": live_revision,
                "revision_checked": False,
                "conflicts": [],
                "promoted": False,
                "external_effects": [],
                "events": ["HUMAN_COMMIT", "REFUSED_BEFORE_DRAFT"],
            },
        }

    draft = apply_patch(base, case["agent"]["writes"])
    live_after_draft_write = dict(base)
    human_after_draft = apply_patch(live_after_draft_write, case["human"]["writes"])
    human_revision = case["human"].get("revision_after_commit", "r1")
    touched = set(case["agent"]["writes"]) | set(case["agent"]["reads"])
    conflicts = sorted(touched.intersection(case["human"]["writes"]))
    if conflicts:
        staged = {
            "status": "CONFLICT_HOLD",
            "reason": "OVERLAPPING_READ_OR_WRITE",
            "draft_created": True,
            "draft": draft,
            "live_after_draft_write": live_after_draft_write,
            "live_revision_after_draft_write": "r0",
            "live_after_human_commit": human_after_draft,
            "final": human_after_draft,
            "final_revision": human_revision,
            "revision_checked": True,
            "conflicts": conflicts,
            "promoted": False,
            "external_effects": [],
            "events": ["DRAFT_CREATED", "DRAFT_WRITE_PRIVATE", "HUMAN_COMMIT", "REVISION_CHECK", "CONFLICT_SURFACED"],
        }
    elif not app["explicit_promotion"]:
        staged = {
            "status": "HOLD_PROMOTION_NOT_AUTHORIZED",
            "reason": "NO_EXPLICIT_PROMOTION",
            "draft_created": True,
            "draft": draft,
            "live_after_draft_write": live_after_draft_write,
            "live_revision_after_draft_write": "r0",
            "live_after_human_commit": human_after_draft,
            "final": human_after_draft,
            "final_revision": human_revision,
            "revision_checked": True,
            "conflicts": [],
            "promoted": False,
            "external_effects": [],
            "events": ["DRAFT_CREATED", "DRAFT_WRITE_PRIVATE", "HUMAN_COMMIT", "REVISION_CHECK", "PROMOTION_HELD"],
        }
    else:
        final = apply_patch(human_after_draft, case["agent"]["writes"])
        staged = {
            "status": "PROMOTED",
            "reason": "DISJOINT_REVISION_MERGED",
            "draft_created": True,
            "draft": draft,
            "live_after_draft_write": live_after_draft_write,
            "live_revision_after_draft_write": "r0",
            "live_after_human_commit": human_after_draft,
            "final": final,
            "final_revision": next_revision(human_revision),
            "revision_checked": True,
            "conflicts": [],
            "promoted": True,
            "external_effects": [],
            "events": ["DRAFT_CREATED", "DRAFT_WRITE_PRIVATE", "HUMAN_COMMIT", "REVISION_CHECK", "EXPLICIT_PROMOTION"],
        }
    return {"case_id": case["id"], "direct": direct, "staged": staged}


def main():
    source, destination = sys.argv[1:3]
    with open(source, encoding="utf-8") as stream:
        cases = json.load(stream)
    result = {"schema": "issue-7409-t0-candidate-v1", "rows": [run_case(case) for case in cases]}
    with open(destination, "w", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps({"schema": result["schema"], "row_count": len(result["rows"]), "output": destination}, sort_keys=True))


if __name__ == "__main__":
    main()
