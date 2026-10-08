#!/usr/bin/env python3
"""Independent raw-only verifier for Issue #6405 T0; does not import candidate.py."""
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ALLOCATION = "APPROVAL-SEQUENCE-DISCRIMINATION-6405-T0-20261002-01"
BASE = "d7e8a932da27e7f271920de409b079fedc75dee1"
IMAGE_ID = "sha256:d8c51b45569cc4fdf0f5d82ae285c3fbb20fae8525d6fab0cebadca171b3bebe"
DIFF_FIELDS = ("recipient", "target", "effect", "scope", "expiry")
FAMILY_FIELDS = ("principal", "recipient", "target", "effect", "scope")


def _digest(obj):
    body = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(body).hexdigest()


def _groups(items):
    expected = {}
    idx = 0
    group_number = 0
    while idx < len(items):
        current = items[idx]
        if current["consequential"]:
            idx += 1
            continue
        family = tuple(current[name] for name in FAMILY_FIELDS)
        end = idx + 1
        while end < len(items):
            nxt = items[end]
            if nxt["consequential"] or tuple(nxt[name] for name in FAMILY_FIELDS) != family:
                break
            end += 1
        if end - idx > 1:
            group_number += 1
            label = f"B{group_number:02d}"
            for member in items[idx:end]:
                expected[member["request_id"]] = label
        idx = end
    return expected


def audit(raw, fixture):
    errors = []
    def require(ok, message):
        if not ok:
            errors.append(message)

    require(raw.get("schema") == "approval-sequence-discrimination-raw-v1", "schema")
    require(raw.get("allocation") == ALLOCATION, "allocation")
    require(raw.get("base") == BASE, "base")
    require(raw.get("image_id") == IMAGE_ID, "image identity")
    canonical_fixture = json.dumps(fixture, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    require(raw.get("fixture_sha256") == hashlib.sha256(canonical_fixture).hexdigest(), "fixture digest")
    requests = fixture.get("requests", [])
    required = fixture.get("required_fields", [])
    require(tuple(required) == ("principal", "recipient", "target", "effect", "scope", "expiry"), "required field manifest")
    ids = [q.get("request_id") for q in requests]
    require(len(ids) == 9 and len(ids) == len(set(ids)), "request inventory")
    arms = raw.get("arms", {})
    require(set(arms) == {"A", "B", "C"}, "arm inventory")
    batch_ids = _groups(requests)
    prior = {}
    previous = None
    receipt_ids = set()
    for request in requests:
        rid = request["request_id"]
        values = {name: request[name] for name in required}
        request_digest = _digest({"request_id": rid, **{k: request[k] for k in ("principal", *DIFF_FIELDS)}})
        supersedes = request.get("supersedes")
        supersedes_digest = prior.get(supersedes) if supersedes else None
        changed = [] if previous is None else [field for field in DIFF_FIELDS if previous[field] != request[field]]
        for arm in ("A", "B", "C"):
            rows = arms.get(arm, [])
            matches = [row for row in rows if row.get("request_id") == rid]
            require(len(matches) == 1, f"{arm}:{rid} occurrence")
            if len(matches) != 1:
                continue
            row = matches[0]
            require(row.get("fields") == values, f"{arm}:{rid} exact displayed fields")
            require(row.get("consequential") is request["consequential"], f"{arm}:{rid} consequence class")
            require(row.get("scripted_response") == request["response"], f"{arm}:{rid} scripted response")
            require(row.get("controls") == ["approve_this_effect", "deny", "cancel"], f"{arm}:{rid} deny/cancel preserved")
            expected_highlights = changed if arm == "B" else []
            require(row.get("highlight_fields") == expected_highlights, f"{arm}:{rid} changed-field salience")
            expected_batch = batch_ids.get(rid) if arm == "C" else None
            require(row.get("batch_id") == expected_batch, f"{arm}:{rid} batch eligibility")
            require(row.get("request_digest") == request_digest, f"{arm}:{rid} request digest")
            require(row.get("supersedes_request_id") == supersedes, f"{arm}:{rid} supersession source")
            require(row.get("supersedes_digest") == supersedes_digest, f"{arm}:{rid} predecessor digest")
            receipt = row.get("receipt")
            if request["response"] == "deny":
                require(receipt is None, f"{arm}:{rid} denial minted receipt")
            else:
                require(isinstance(receipt, dict), f"{arm}:{rid} missing explicit receipt")
                if isinstance(receipt, dict):
                    require(receipt.get("principal") == request["principal"], f"{arm}:{rid} receipt principal")
                    require(receipt.get("request_digest") == request_digest, f"{arm}:{rid} receipt digest binding")
                    require(receipt.get("scope") == {k: request[k] for k in DIFF_FIELDS}, f"{arm}:{rid} receipt scope")
                    require(receipt.get("expires_at") == request["expiry"], f"{arm}:{rid} receipt expiry")
                    token = receipt.get("receipt_id")
                    require(token not in receipt_ids, f"{arm}:{rid} duplicate receipt id")
                    receipt_ids.add(token)
            if arm == "C" and expected_batch is not None:
                require(row.get("batch_level_receipt") is None, f"C:{rid} batch-wide authority")
        prior[rid] = request_digest
        previous = request
    for arm in ("A", "B", "C"):
        rows = arms.get(arm, [])
        require(len(rows) == len(requests), f"{arm} row count")
        require({r.get("request_id") for r in rows} == set(ids), f"{arm} exact request coverage")
    require(raw.get("scope_boundary") == "scripted synthetic protocol fidelity only; no human behavior or real authority", "scope boundary")
    return errors


def mutation_controls(raw, fixture):
    cases = []
    def copy():
        return json.loads(json.dumps(raw))
    bad = copy(); bad["arms"]["A"][0]["fields"].pop("expiry", None); cases.append(("omitted_field", bad))
    bad = copy(); bad["arms"]["A"][0]["fields"]["recipient"] = "attacker"; cases.append(("swapped_recipient", bad))
    bad = copy(); bad["arms"]["B"][1]["highlight_fields"] = ["effect"]; cases.append(("stale_highlight", bad))
    bad = copy(); bad["arms"]["C"][5]["batch_id"] = bad["arms"]["C"][0]["batch_id"]; cases.append(("overbroad_batch", bad))
    bad = copy(); bad["arms"]["B"][5]["receipt"]["request_digest"] = bad["arms"]["B"][0]["request_digest"]; cases.append(("prior_receipt_reuse", bad))
    return {name: bool(audit(candidate, fixture)) for name, candidate in cases}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, default=ROOT / "fixture.json")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.raw.read_text())
    fixture = json.loads(args.fixture.read_text())
    errors = audit(raw, fixture)
    controls = mutation_controls(raw, fixture)
    rejected = all(controls.values())
    result = {"audit": "PASS_METHOD_SCOPED" if not errors and rejected else "FAIL_METHOD",
              "errors": errors, "mutation_controls_rejected": controls,
              "raw_sha256": hashlib.sha256(args.raw.read_bytes()).hexdigest(),
              "scope": "finite scripted fixture only; no human behavior or real authority"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["audit"] == "PASS_METHOD_SCOPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
