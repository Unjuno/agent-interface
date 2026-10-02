#!/usr/bin/env python3
"""Deterministic no-participant approval presentation fixture for Issue #6405 T0."""
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ALLOCATION = "APPROVAL-SEQUENCE-DISCRIMINATION-6405-T0-20261002-01"
BASE = "d7e8a932da27e7f271920de409b079fedc75dee1"
IMAGE_ID = "sha256:d8c51b45569cc4fdf0f5d82ae285c3fbb20fae8525d6fab0cebadca171b3bebe"
EFFECT_FIELDS = ("recipient", "target", "effect", "scope", "expiry")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def request_payload(request):
    return {"request_id": request["request_id"], **{k: request[k] for k in ("principal", *EFFECT_FIELDS)}}


def _batch_groups(requests):
    """Return groups of consecutive, same-principal nonconsequential request families."""
    families = []
    family_fields = ("principal", "recipient", "target", "effect", "scope")
    for request in requests:
        if request["consequential"]:
            families.append(None)
        else:
            families.append(tuple(request[k] for k in family_fields))
    groups = {}
    i = 0
    number = 0
    while i < len(requests):
        if families[i] is None:
            i += 1
            continue
        j = i + 1
        while j < len(requests) and families[j] == families[i]:
            j += 1
        if j - i >= 2:
            number += 1
            batch_id = f"B{number:02d}"
            for k in range(i, j):
                groups[requests[k]["request_id"]] = batch_id
        i = j
    return groups


def build_raw(fixture):
    requests = fixture["requests"]
    if len({r["request_id"] for r in requests}) != len(requests):
        raise ValueError("duplicate request id")
    groups = _batch_groups(requests)
    prior_by_id = {}
    arm_rows = {arm: [] for arm in ("A", "B", "C")}
    previous = None
    for request in requests:
        payload = request_payload(request)
        request_digest = digest(payload)
        if request["supersedes"] is not None:
            if request["supersedes"] not in prior_by_id:
                raise ValueError("superseded request is not earlier in frozen sequence")
            supersedes_digest = prior_by_id[request["supersedes"]]
        else:
            supersedes_digest = None
        changed = [] if previous is None else [
            key for key in EFFECT_FIELDS if previous[key] != request[key]
        ]
        for arm in ("A", "B", "C"):
            receipt = None
            if request["response"] == "approve":
                receipt = {
                    "receipt_id": f"G-{arm}-{request['request_id']}",
                    "principal": request["principal"],
                    "request_digest": request_digest,
                    "scope": {key: request[key] for key in EFFECT_FIELDS},
                    "expires_at": request["expiry"],
                }
            arm_rows[arm].append({
                "request_id": request["request_id"],
                "fields": {key: request[key] for key in fixture["required_fields"]},
                "consequential": request["consequential"],
                "scripted_response": request["response"],
                "highlight_fields": changed if arm == "B" else [],
                "batch_id": groups.get(request["request_id"]) if arm == "C" else None,
                "controls": ["approve_this_effect", "deny", "cancel"],
                "request_digest": request_digest,
                "supersedes_request_id": request["supersedes"],
                "supersedes_digest": supersedes_digest,
                "receipt": receipt,
            })
        prior_by_id[request["request_id"]] = request_digest
        previous = request
    fixture_bytes = canonical(fixture)
    return {
        "schema": "approval-sequence-discrimination-raw-v1",
        "allocation": ALLOCATION,
        "base": BASE,
        "image_id": IMAGE_ID,
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "arms": arm_rows,
        "scope_boundary": "scripted synthetic protocol fidelity only; no human behavior or real authority",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=ROOT / "fixture.json")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    fixture = json.loads(args.fixture.read_text())
    raw = build_raw(fixture)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"candidate": "PASS_GENERATED", "rows": sum(map(len, raw["arms"].values())),
                      "fixture_sha256": raw["fixture_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
