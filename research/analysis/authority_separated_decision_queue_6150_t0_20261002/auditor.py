import copy
import json
import sys
from pathlib import Path


POLICIES = ("IMMEDIATE", "FIFO", "EARLIEST_DEADLINE", "BOUNDED_BATCH")


def oracle(f):
    cards = [x for x in f["events"] if x["type"] == "arrive"]
    cancelled = {(x["id"], x["version"]): x["at"] for x in f["events"] if x["type"] == "cancel"}
    answers = {}
    for p in POLICIES:
        t, todo, order, expired, stale = 0, list(cards), [], [], []
        alert_done = False
        while todo:
            alert = f["urgent_release"]
            if not alert_done:
                t = max(t, alert["at"]) + alert["duration"]
                alert_done = True
            ready = [x for x in todo if x["at"] <= t]
            if not ready:
                t = min(x["at"] for x in todo)
                ready = [x for x in todo if x["at"] <= t]
            if p == "BOUNDED_BATCH":
                w = [x for x in todo if x["at"] <= t + f["batch_wait"]]
                t = max(t, *(x["at"] for x in w))
                ready = [x for x in todo if x["at"] <= t]
            if p == "EARLIEST_DEADLINE" or p == "BOUNDED_BATCH":
                chosen = min(ready, key=lambda x: (x["deadline"], x["at"], x["id"], x["version"]))
            else:
                chosen = min(ready, key=lambda x: (x["at"], x["id"], x["version"]))
            todo.remove(chosen)
            key = (chosen["id"], chosen["version"])
            if key in cancelled and cancelled[key] <= t:
                stale.append(key)
                continue
            finish = max(t, chosen["at"]) + chosen["duration"]
            if finish > chosen["deadline"]:
                expired.append(key)
                t = finish
                continue
            order.append((key, t, finish))
            t = finish
        answers[p] = {"order": order, "expired": sorted(expired), "cancelled": sorted(stale)}
    return answers


def audit(f, result):
    if result.get("schema") != "authority-queue-result-v1" or set(result.get("rows", {})) != set(POLICIES):
        raise ValueError("shape/policy set")
    expected = oracle(f)
    source = {(x["id"], x["version"]): x for x in f["events"] if x["type"] == "arrive"}
    for p in POLICIES:
        row = result["rows"][p]
        if row["urgent"] != [{"id": "R0", "start": 2, "end": 3, "released": True}]:
            raise ValueError("urgent release was deferred or altered")
        actual_order = [((x["id"], x["version"]), x["start"], x["end"]) for x in row["reviews"]]
        if actual_order != expected[p]["order"]:
            raise ValueError("review schedule differs from independent event oracle")
        if sorted((x["id"], x["version"]) for x in row["expired"]) != expected[p]["expired"]:
            raise ValueError("expiry mismatch")
        if sorted((x["id"], x["version"]) for x in row["cancelled"]) != expected[p]["cancelled"]:
            raise ValueError("cancellation mismatch")
        seen = set()
        for r in row["receipts"]:
            key = (r["id"], r["version"])
            if key in seen or key not in source:
                raise ValueError("duplicate or unknown receipt")
            seen.add(key)
            c = source[key]
            if any(r.get(k) != c[k] for k in ("principal", "target", "effect", "decision")):
                raise ValueError("receipt binding mismatch")
            if key in expected[p]["expired"] or key in expected[p]["cancelled"] or r["decision"] == "no_response":
                raise ValueError("receipt for ineligible card")
        expected_receipts = {k for k, c in source.items() if c["decision"] != "no_response" and k not in expected[p]["expired"] and k not in expected[p]["cancelled"] and any((q[0] == k) for q in expected[p]["order"])}
        if seen != expected_receipts:
            raise ValueError("missing/extra card decision")
        for a in row["effect_attempts"]:
            key = (a["id"], a["version"])
            card = source.get(key)
            if not card or card["decision"] != "accept" or any(a.get(k) != card[k] for k in ("principal", "target", "effect")) or a.get("receipt_id") != f"{key[0]}:{key[1]}":
                raise ValueError("effect attempt not bound to exact accepted card")
        expected_attempts = {k for k in expected_receipts if source[k]["decision"] == "accept"}
        actual_attempts = {(a["id"], a["version"]) for a in row["effect_attempts"]}
        if actual_attempts != expected_attempts or len(actual_attempts) != len(row["effect_attempts"]):
            raise ValueError("accept/effect attempt cardinality mismatch")
    return {"status": "METHOD_PASS_SCOPED", "policies": len(POLICIES), "corruptions_rejected": 5}


def corruption_controls(f, result):
    mutations = []
    a = copy.deepcopy(result); a["rows"]["IMMEDIATE"]["receipts"][0]["id"] = "B"; mutations.append(a)
    a = copy.deepcopy(result); a["rows"]["IMMEDIATE"]["receipts"][0]["version"] = 99; mutations.append(a)
    a = copy.deepcopy(result); a["rows"]["IMMEDIATE"]["effect_attempts"][0]["target"] = "wrong"; mutations.append(a)
    a = copy.deepcopy(result); a["rows"]["IMMEDIATE"]["receipts"].append(copy.deepcopy(a["rows"]["IMMEDIATE"]["receipts"][0])); mutations.append(a)
    a = copy.deepcopy(result); a["rows"]["IMMEDIATE"]["urgent"][0]["start"] = 99; mutations.append(a)
    rejected = 0
    for mutant in mutations:
        try:
            audit(f, mutant)
        except (ValueError, KeyError, TypeError):
            rejected += 1
    if rejected != 5:
        raise ValueError(f"corruption rejection count {rejected}/5")
    return rejected


if __name__ == "__main__":
    fx, raw, out = map(Path, sys.argv[1:4])
    f = json.loads(fx.read_text(encoding="utf-8"))
    result = json.loads(raw.read_text(encoding="utf-8"))
    verdict = audit(f, result)
    verdict["corruption_rejections"] = corruption_controls(f, result)
    out.write_text(json.dumps(verdict, sort_keys=True, indent=2) + "\n", encoding="utf-8")

