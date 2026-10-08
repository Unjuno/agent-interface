"""Raw-only auditor; independently checks matched context identities and controls."""
import hashlib
import json
import sys
from pathlib import Path


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha(value):
    return hashlib.sha256(value).hexdigest()


def audit(fixture_bytes, raw):
    fixture = json.loads(fixture_bytes)
    errors = []
    expected_count = len(fixture["conditions"]) * len(fixture["conflict_depths"]) * len(fixture["arms"])
    if raw.get("schema_version") != 1 or raw.get("allocation_id") != fixture["allocation_id"]:
        errors.append("ROOT_IDENTITY")
    if raw.get("fixture_sha256") != sha(fixture_bytes):
        errors.append("FIXTURE_DIGEST")
    rows = raw.get("rows", [])
    if len(rows) != expected_count:
        errors.append("DENOMINATOR")
    expected_order = [(c["id"], d, a) for c in fixture["conditions"] for d in fixture["conflict_depths"] for a in fixture["arms"]]
    observed_order = [(row.get("condition_id"), row.get("depth"), row.get("arm")) for row in rows]
    if observed_order != expected_order:
        errors.append("ROW_ORDER_OR_IDENTITY")
    expected = {}
    for condition in fixture["conditions"]:
        for depth in fixture["conflict_depths"]:
            for arm in fixture["arms"]:
                expected[(condition["id"], depth, arm)] = condition
    seen = set()
    by_stratum = {}
    for row in rows:
        key = (row.get("condition_id"), row.get("depth"), row.get("arm"))
        condition = expected.get(key)
        if condition is None or key in seen:
            errors.append("ROW_IDENTITY_OR_DUPLICATE")
            continue
        seen.add(key)
        body = row.get("body", {})
        encoded = canonical(body).encode("utf-8")
        if row.get("body_sha256") != sha(encoded) or row.get("utf8_bytes") != len(encoded):
            errors.append("BODY_DIGEST_OR_LENGTH")
        cue = encoded.find(b'"current"')
        if cue != row.get("current_cue_byte_offset"):
            errors.append("CURRENT_CUE_OFFSET")
        if body.get("query") != condition["query"] or body.get("current") != {"id":"CURRENT","value":condition["final_value"],"status":"OBSERVED"}:
            errors.append("TASK_OR_FINAL_STATE")
        if body.get("authority") != fixture["authority"] or body["authority"].get("execution_authority") is not False:
            errors.append("AUTHORITY")
        if condition["kind"] == "history_required":
            if body.get("baseline") != {"id":"BASELINE","value":condition["baseline_value"],"status":"OBSERVED"}:
                errors.append("BASELINE_LOSS")
            if condition["baseline_value"] not in condition["query"] or condition["final_value"] not in condition["query"] or row.get("expected") != f'{condition["baseline_value"]}_TO_{condition["final_value"]}':
                errors.append("HISTORY_REQUIRED_QUERY")
        elif body.get("baseline") is not None:
            errors.append("UNEXPECTED_BASELINE")
        if row.get("expected") != condition["expected"] or row.get("kind") != condition["kind"]:
            errors.append("ORACLE_LABEL")
        depth = row["depth"]
        arm = row["arm"]
        episodes, ledger = body.get("episodes"), body.get("ledger")
        if arm == "FULL_CONFLICTING_HISTORY":
            if len(episodes) != depth or any(item.get("status") != "SUPERSEDED" for item in episodes): errors.append("CONFLICT_SCHEDULE")
        elif arm == "NONCONFLICTING_HISTORY":
            if len(episodes) != depth or any(item.get("status") != "OBSERVED" or not item.get("value", "").startswith("UNRELATED_") for item in episodes): errors.append("NEUTRAL_HISTORY_CONTROL")
        else:
            if episodes: errors.append("UNEXPECTED_EPISODES")
        if arm == "SOURCE_LINKED_DELTA":
            if len(ledger) != depth or any(item.get("status") != "SUPERSEDED" or item.get("current_id") != "CURRENT" for item in ledger): errors.append("LEDGER_LINEAGE")
        elif ledger:
            errors.append("UNEXPECTED_LEDGER")
        by_stratum.setdefault((condition["id"], depth), []).append(row)
    if len(seen) != expected_count:
        errors.append("MISSING_ROWS")
    for key, group in by_stratum.items():
        if len(group) != len(fixture["arms"]):
            errors.append("MATCHED_GROUP_SIZE")
            continue
        if len({row["body"]["current"]["value"] for row in group}) != 1 or len({row["body"]["query"] for row in group}) != 1:
            errors.append("MATCHED_TRUTH_OR_QUERY")
        offsets = {row["current_cue_byte_offset"] for row in group}
        if len(offsets) != 1:
            errors.append("MATCHED_CUE_OFFSET")
        if len({row["utf8_bytes"] for row in group}) != 1:
            errors.append("MATCHED_BYTE_LENGTH")
    control = raw.get("position_control", {})
    if control.get("id") != fixture["position_control"]["id"] or control.get("offset_differs") is not True:
        errors.append("POSITION_POSITIVE_CONTROL")
    pos_a = '{"padding":"","task":"position control","current":{"id":"CURRENT","value":"TARGET_Z"}}'
    pos_b = '{"task":"position control","padding":"' + (' ' * 80) + '","current":{"id":"CURRENT","value":"TARGET_Z"}}'
    if control.get("before_sha256") != sha(pos_a.encode()) or control.get("after_sha256") != sha(pos_b.encode()):
        errors.append("POSITION_CONTROL_BYTES")
    mutations = [
        ("alter_final_truth", lambda x: x["rows"][0]["body"]["current"].update(value="TARGET_MUTATED")),
        ("move_current_cue", lambda x: x["rows"][0]["body"].update(current={"id":"CURRENT","value":"TARGET_Z","status":"OBSERVED"}, zzz="move")),
        ("drop_episode", lambda x: x["rows"][2]["body"]["episodes"].pop()),
        ("relabel_inferred_as_observed", lambda x: x["rows"][11]["body"]["ledger"][0].update(status="OBSERVED")),
    ]
    checks=[]
    for name, mutate in mutations:
        altered=json.loads(json.dumps(raw))
        try: mutate(altered)
        except (IndexError, KeyError): pass
        result=audit_without_mutations(fixture_bytes, altered)
        checks.append({"name":name,"rejected":bool(result)})
    return {"errors":errors,"rows":len(rows),"expected_rows":expected_count,"mutation_checks":checks,
            "status":"PASS_FIXTURE_METHOD_SCOPED" if not errors and all(item["rejected"] for item in checks) else "FAIL_FIXTURE_AUDIT"}


def audit_without_mutations(fixture_bytes, raw):
    # Avoid recursive mutation testing while preserving the full structural audit.
    fixture=json.loads(fixture_bytes); errors=[]
    if raw.get("fixture_sha256") != sha(fixture_bytes): errors.append("FIXTURE_DIGEST")
    if len(raw.get("rows",[])) != len(fixture["conditions"])*len(fixture["conflict_depths"])*len(fixture["arms"]): errors.append("DENOMINATOR")
    expected={(c["id"],d,a):c for c in fixture["conditions"] for d in fixture["conflict_depths"] for a in fixture["arms"]}
    seen=set()
    expected_order=[(c["id"],d,a) for c in fixture["conditions"] for d in fixture["conflict_depths"] for a in fixture["arms"]]
    observed_order=[(x.get("condition_id"),x.get("depth"),x.get("arm")) for x in raw.get("rows",[])]
    if observed_order != expected_order: errors.append("ORDER")
    for row in raw.get("rows",[]):
        key=(row.get("condition_id"),row.get("depth"),row.get("arm")); c=expected.get(key)
        if c is None or key in seen: errors.append("ROW_IDENTITY"); continue
        seen.add(key); b=row["body"]; encoded=canonical(b).encode(); depth=row["depth"]; arm=row["arm"]
        if b.get("current") != {"id":"CURRENT","value":c["final_value"],"status":"OBSERVED"}: errors.append("FINAL")
        if row.get("current_cue_byte_offset") != encoded.find(b'"current"'): errors.append("OFFSET")
        if row.get("body_sha256") != sha(encoded): errors.append("DIGEST")
        if c["kind"]=="history_required" and (b.get("baseline") != {"id":"BASELINE","value":c["baseline_value"],"status":"OBSERVED"} or c["baseline_value"] not in c["query"] or c["final_value"] not in c["query"] or row.get("expected") != f'{c["baseline_value"]}_TO_{c["final_value"]}'): errors.append("BASELINE")
        if arm=="FULL_CONFLICTING_HISTORY" and (len(b.get("episodes",[]))!=depth or any(x.get("status")!="SUPERSEDED" for x in b.get("episodes",[]))): errors.append("CONFLICT")
        if arm=="NONCONFLICTING_HISTORY" and (len(b.get("episodes",[]))!=depth or any(x.get("status")!="OBSERVED" for x in b.get("episodes",[]))): errors.append("NEUTRAL")
        if arm=="SOURCE_LINKED_DELTA" and (len(b.get("ledger",[]))!=depth or any(x.get("status")!="SUPERSEDED" or x.get("current_id")!="CURRENT" for x in b.get("ledger",[]))): errors.append("LEDGER")
        if arm!="SOURCE_LINKED_DELTA" and b.get("ledger"): errors.append("LEDGER_UNEXPECTED")
        if arm=="CURRENT_ONLY" and len(b.get("padding", "")) != depth*128 - 4 if depth else bool(b.get("padding")): errors.append("NEUTRAL_VOLUME")
        if arm in ("FULL_CONFLICTING_HISTORY", "NONCONFLICTING_HISTORY", "SOURCE_LINKED_DELTA") and depth and len(b.get("padding", "")) + len(canonical(b.get("episodes",[]) if arm != "SOURCE_LINKED_DELTA" else b.get("ledger",[]))) != depth*128: errors.append("MATCHED_VOLUME")
        if row.get("utf8_bytes") != len(encoded) or row.get("expected") != c["expected"] or row.get("kind") != c["kind"]: errors.append("METADATA")
    return errors


def main():
    if len(sys.argv)!=4: raise SystemExit("usage: audit.py FIXTURE RAW OUTPUT")
    fixture=Path(sys.argv[1]).read_bytes(); raw=json.loads(Path(sys.argv[2]).read_bytes())
    result=audit(fixture,raw)
    with Path(sys.argv[3]).open("x",encoding="utf-8") as stream:
        json.dump(result,stream,indent=2); stream.write("\n")
    if result["status"]!="PASS_FIXTURE_METHOD_SCOPED": raise SystemExit(1)


if __name__=="__main__": main()
