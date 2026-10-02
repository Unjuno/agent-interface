"""Independent raw-only enumerator for Issue #6689 T0."""
import json
import sys
from functools import lru_cache
from pathlib import Path

NAMES = ("generation", "sealed", "invalidated", "mandatory_fail", "mandatory_all_pass",
         "source_a_negative", "source_b_negative", "source_a_closed", "source_b_closed",
         "source_a_timeout", "source_b_timeout")
ROOT = (0, False, False, False, False, False, False, False, False, False, False)


def independent_edges(x):
    g, z, inv, fail, passed, na, nb, ca, cb, ta, tb = x
    e = []
    if not fail and not passed:
        e += [x[:3] + (True,) + x[4:], x[:4] + (True,) + x[5:]]
    if not ca:
        if not na: e.append(x[:5] + (True,) + x[6:])
        e.append(x[:7] + (True,) + x[8:])
        if not ta: e.append(x[:9] + (True,) + x[10:])
    if not cb:
        if not nb: e.append(x[:6] + (True,) + x[7:])
        e.append(x[:8] + (True,) + x[9:])
        if not tb: e.append(x[:10] + (True,))
    if not z: e.append(x[:1] + (True,) + x[2:])
    if g == 0 and not z and not inv:
        e.append((1, False, True, False, False, False, False, False, False, False, False))
    return e


def terminal_independent(x):
    if x[3] or x[5] or x[6]: return "FAIL"
    if x[4] and x[7] and x[8]: return "PASS"
    return "UNKNOWN"


def enumerate_contract():
    parents = {ROOT: (None, None)}
    work = [ROOT]
    for x in work:
        for y in independent_edges(x):
            if y not in parents:
                parents[y] = (x, event_name(x, y))
                work.append(y)
    @lru_cache(None)
    def endings(x):
        result = {terminal_independent(x)}
        for y in independent_edges(x): result.update(endings(y))
        return tuple(sorted(result))
    rows = {}
    paths = {}
    for x in parents:
        path = []
        current = x
        while parents[current][0] is not None:
            parent, event = parents[current]
            path.append(event)
            current = parent
        paths[x] = tuple(reversed(path))
    for x in parents:
        outcomes = endings(x)
        if len(outcomes) == 1: label = "STABLE_FINAL_" + outcomes[0]
        elif x[4] and not x[3] and not x[5] and not x[6] and not (x[7] and x[8]): label = "CLOSED_FRONTIER_REQUIRED"
        else: label = "PROVISIONAL"
        pending = ([] if x[3] or x[4] else ["mandatory_check_vector"])
        if not x[7]: pending.append("source_a_completion")
        if not x[8]: pending.append("source_b_completion")
        rows[x] = (outcomes, label, pending, paths[x])
    return rows


def event_name(before, after):
    if before[0] == 0 and after[0] == 1: return "generation_invalidated"
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    names = {1: "generation_sealed", 3: "mandatory_fail",
             4: "mandatory_all_pass", 5: "source_a_negative", 6: "source_b_negative",
             7: "source_a_closed", 8: "source_b_closed", 9: "source_a_timeout", 10: "source_b_timeout"}
    if len(changed) != 1 or changed[0] not in names: raise ValueError("invalid edge")
    return names[changed[0]]


def validate(raw):
    if raw.get("schema") != "prefix-stability-6689-raw-v1": return False
    expected = enumerate_contract()
    seen = set()
    for row in raw.get("rows", []):
        st = row.get("state", {})
        if st == {"contract_known": False}:
            if row.get("terminal_outcomes") != ["UNKNOWN"] or row.get("classification") != "UNKNOWN" or row.get("pending_obligations") != ["continuation_contract"] or row.get("representative_prefix") != []: return False
            if "unknown-contract" in seen: return False
            seen.add("unknown-contract")
            continue
        try: x = tuple(st[n] for n in NAMES)
        except Exception: return False
        if x in seen or x not in expected: return False
        seen.add(x)
        outcomes, label, pending, prefix = expected[x]
        if row.get("terminal_outcomes") != list(outcomes) or row.get("classification") != label or row.get("pending_obligations") != pending or row.get("representative_prefix") != list(prefix): return False
    return len(seen) == len(expected) + 1


def audit(raw):
    if not validate(raw): return {"status": "FAIL_METHOD", "errors": ["raw_reconstruction_mismatch"]}
    # Four prescribed corruptions must each fail raw reconstruction.
    checks = {}
    rows = raw["rows"]
    labels = ("drop_or_forge_mandatory", "forge_source_closed", "relabel_stale_generation", "timeout_or_partial_as_complete")
    def select(rows, predicate):
        return next(r for r in rows if r["state"] != {"contract_known": False} and predicate(r["state"]))
    for label in labels:
        altered = json.loads(json.dumps(raw))
        rows2 = altered["rows"]
        if label == "drop_or_forge_mandatory":
            target = select(rows2, lambda s: s.get("mandatory_fail"))
            target["state"]["mandatory_fail"] = False
        elif label == "forge_source_closed":
            target = select(rows2, lambda s: not s.get("source_a_closed"))
            target["state"]["source_a_closed"] = True
        elif label == "relabel_stale_generation":
            target = select(rows2, lambda s: s.get("invalidated") and s.get("generation") == 1)
            target["state"]["generation"] = 0
        else:
            target = select(rows2, lambda s: s.get("source_a_timeout") and not s.get("source_a_closed"))
            target["state"]["source_a_closed"] = True
        checks[label] = not validate(altered)
    if not all(checks.values()): return {"status": "FAIL_METHOD", "errors": ["mutation_survived"], "controls": checks}
    hist = {}
    for r in rows:
        hist[r["classification"]] = hist.get(r["classification"], 0) + 1
    return {"status": "PASS_METHOD_SCOPED", "errors": [], "state_count": len(rows)-1,
            "classifications": hist, "mutation_controls_rejected": checks}


def main():
    src = Path(sys.argv[1]); dst = Path(sys.argv[2])
    if dst.exists(): raise SystemExit("refusing to overwrite audit output")
    raw = json.loads(src.read_text(encoding="utf-8"))
    result = audit(raw)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(result, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS_METHOD_SCOPED" else 1)


if __name__ == "__main__": main()
