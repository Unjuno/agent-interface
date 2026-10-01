"""Independent raw-only oracle for Issue #5318 T0; imports no candidate code."""
import json
import sys

POLICIES = ("RAW_COALESCE", "GLOBAL_SERIAL", "SEMANTIC_SERIALIZABILITY",
            "OPTIMISTIC_VALIDATE_COMMIT", "UNKNOWN_AS_CONFLICT")


def serial(initial, txs):
    out = dict(initial)
    for t in txs:
        if t["kind"] == "set":
            out[t["key"]] = t["value"]
        elif t["kind"] == "add":
            out[t["key"]] += t["delta"]
        elif t["kind"] == "conditional_set":
            v = out[t["reads"][0]]
            if (t["guard"] == "x-zero" or t["guard"] == "y-zero") and v == 0:
                out[t["key"]] = t["value"]
            if t["guard"] == "ticket-one" and v == 1:
                out[t["key"]] = t["value"]
    return out


def parallel(initial, txs):
    snap = dict(initial)
    proposed = []
    for t in txs:
        local = serial(snap, [t])
        proposed.append((t, local))
    out = dict(snap)
    for key in snap:
        writers = [(t, local) for t, local in proposed if key in t["writes"] and local[key] != snap[key]]
        if writers and all(t["kind"] == "add" and t["commute_rule"] == "integer-add-v1" for t, _ in writers):
            out[key] = snap[key] + sum(t["delta"] for t, _ in writers)
        elif writers:
            out[key] = writers[-1][1][key]
    return out


def has_conflict(a, b):
    if a["quality"] != "EXACT" or b["quality"] != "EXACT":
        return True
    aw, bw, ar, br = map(set, (a["writes"], b["writes"], a["reads"], b["reads"]))
    if aw & br or bw & ar:
        return True
    if aw & bw:
        return not (a["kind"] == b["kind"] == "add" and
                    a["commute_rule"] == b["commute_rule"] == "integer-add-v1")
    return False


def oracle(case, policy):
    a, b = case["transactions"]
    serials = [serial(case["initial"], [a, b]), serial(case["initial"], [b, a])]
    if policy == "GLOBAL_SERIAL":
        return "SERIALIZE", serials[0], [a["id"], b["id"]], serials
    if policy == "RAW_COALESCE":
        if a["key"] == b["key"] and a["kind"] == b["kind"]:
            return "COALESCE", serial(case["initial"], [a]), [a["id"]], serials
        return "PARALLEL", parallel(case["initial"], [a, b]), [a["id"], b["id"]], serials
    conflict = has_conflict(a, b)
    cycle = bool(set(a["writes"]) & set(b["reads"]) and set(b["writes"]) & set(a["reads"]))
    if policy == "OPTIMISTIC_VALIDATE_COMMIT" and conflict:
        return "ABORT", dict(case["initial"]), [], serials
    if policy == "UNKNOWN_AS_CONFLICT" and (a["quality"] != "EXACT" or b["quality"] != "EXACT"):
        return "DEFER", dict(case["initial"]), [], serials
    if cycle:
        return "ABORT", dict(case["initial"]), [], serials
    if conflict:
        return "SERIALIZE", serials[0], [a["id"], b["id"]], serials
    return "PARALLEL", parallel(case["initial"], [a, b]), [a["id"], b["id"]], serials


def audit(path):
    with open(path, "rb") as stream:
        raw = stream.read()
    rows = [json.loads(line) for line in raw.splitlines()]
    errors = []
    expected_pairs = {(s, p) for s in ("disjoint", "commuting_add", "same_set", "write_skew_cycle",
                                        "unknown_overlap", "delayed_irreversible") for p in POLICIES}
    actual_pairs = {(r.get("scenario"), r.get("policy")) for r in rows}
    if len(rows) != 30 or actual_pairs != expected_pairs or len(actual_pairs) != len(rows):
        errors.append("ROW_COVERAGE")
    for r in rows:
        try:
            expected = oracle(r, r["policy"])
            actual = (r["decision"], r["final"], r["committed"], r["legal_serial_finals"])
            if actual != expected:
                errors.append("ROW_RECONSTRUCTION:" + str((r["scenario"], r["policy"])))
            if r["parallel_count"] != int(r["decision"] == "PARALLEL"):
                errors.append("PARALLEL_COUNT")
            if r["delayed_effects"] != [t["id"] for t in r["transactions"] if t["delay"] > 0]:
                errors.append("DELAY_ACCOUNTING")
            if r["irreversible_sources"] != [t["id"] for t in r["transactions"] if t["effect"] == "IRREVERSIBLE"]:
                errors.append("IRREVERSIBLE_ACCOUNTING")
            if r["policy"] in ("SEMANTIC_SERIALIZABILITY", "OPTIMISTIC_VALIDATE_COMMIT", "UNKNOWN_AS_CONFLICT"):
                if r["committed"] and r["decision"] != "DEFER" and r["final"] not in r["legal_serial_finals"]:
                    errors.append("GUARDED_NON_SERIAL_RESULT")
        except (KeyError, TypeError, ValueError):
            errors.append("MALFORMED_ROW")
    return {"rows": len(rows), "errors": errors, "raw_sha256": __import__("hashlib").sha256(raw).hexdigest()}


if __name__ == "__main__":
    result = audit(sys.argv[1])
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if not result["errors"] else 1)

