import argparse
import json
from pathlib import Path


def decide(case, policy):
    if not case["actor_authorized"]:
        return "BLOCKED_FLOW", []
    if (
        case["recipient"] in policy["protected_sinks"]
        and case["integrity"] != policy["minimum_integrity"]
    ):
        return "BLOCKED_FLOW", []
    if case["source_label"] == policy["sensitive_label"]:
        if case["recipient"] is None or case["purpose"] is None:
            return "UNKNOWN_FLOW", []
        matches = [item for item in policy["allowed_contexts"] if
            item["recipient"] == case["recipient"]
            and item["purpose"] == case["purpose"]
            and item["fields"] == case["requested_fields"]
            and case["integrity"] == item["minimum_integrity"]
            and ("explicit_release_revision" not in item
                 or item["explicit_release_revision"] == case["release_revision"])]
        if not matches:
            return "BLOCKED_FLOW", []
        if any("explicit_release_revision" in item for item in matches):
            return "DECLASSIFIED", case["requested_fields"]
        return "ALLOWED", case["requested_fields"]
    return "ALLOWED", case["requested_fields"]


def run(fixture, policy):
    rows = []
    for case in fixture["cases"]:
        for mode in ("ACTOR_ONLY", "LABEL_ONLY", "CONTEXT_BOUND"):
            if mode == "ACTOR_ONLY":
                decision, released = ("ALLOWED", case["requested_fields"]) if case["actor_authorized"] else ("BLOCKED_FLOW", [])
            elif mode == "LABEL_ONLY":
                decision, released = ("ALLOWED", case["requested_fields"]) if case["source_label"] != "PERSONAL" else ("BLOCKED_FLOW", [])
            else:
                decision, released = decide(case, policy)
            rows.append({
                "case_id": case["id"], "mode": mode, "decision": decision,
                "released_fields": released, "source_digest": case["source_digest"],
                "actor": case["actor"], "actor_authorized": case["actor_authorized"],
                "source_label": case["source_label"], "integrity": case["integrity"],
                "requested_fields": case["requested_fields"], "release_revision": case["release_revision"],
                "recipient": case["recipient"], "purpose": case["purpose"]
            })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="fixture.json")
    parser.add_argument("--policy", default="policy.json")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    Path(args.out).write_text(json.dumps(run(fixture, policy), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
