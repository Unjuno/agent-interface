import hashlib
import itertools
import json

STATES = range(3)
ACTIONS = range(2)
PAIRS = list(itertools.product(STATES, ACTIONS))
AUTOMATA = list(itertools.product(STATES, repeat=len(PAIRS)))
ALL_MASK = (1 << len(PAIRS)) - 1

def signature(table, mask):
    return tuple(table[i] if mask & (1 << i) else None for i in range(len(PAIRS)))

def classes(table_ids, mask):
    groups = {}
    for idx in table_ids:
        groups.setdefault(signature(AUTOMATA[idx], mask), []).append(idx)
    return groups

def safe_probe_candidates(mask, safe_mask):
    return [i for i in range(len(PAIRS)) if not mask & (1 << i) and safe_mask & (1 << i)]

def choose_probe(table_ids, mask, safe_mask):
    candidates = safe_probe_candidates(mask, safe_mask)
    if not candidates:
        return None
    before = len(table_ids)
    scored = []
    for pair in candidates:
        outcomes = {}
        for idx in table_ids:
            value = AUTOMATA[idx][pair]
            outcomes.setdefault(value, []).append(idx)
        worst = max(len(v) for v in outcomes.values())
        scored.append((worst, pair, before - worst))
    return min(scored)[1]

def apply_probe(table_ids, mask, pair, table_id):
    value = AUTOMATA[table_id][pair]
    new_mask = mask | (1 << pair)
    return [idx for idx in table_ids if AUTOMATA[idx][pair] == value], new_mask

def run():
    rows = []
    for mask in range(1 << len(PAIRS)):
        for safe_mask in range(1 << len(PAIRS)):
            candidate_ids = list(range(len(AUTOMATA)))
            observed = signature(AUTOMATA[0], mask)
            candidate_ids = [i for i in candidate_ids if signature(AUTOMATA[i], mask) == observed]
            chosen = choose_probe(candidate_ids, mask, safe_mask)
            if chosen is None:
                rows.append({"mask": mask, "safe_mask": safe_mask, "chosen": None,
                             "before": len(candidate_ids), "after": len(candidate_ids),
                             "preserves_unknown": len(candidate_ids) > 1})
                continue
            after_ids, after_mask = apply_probe(candidate_ids, mask, chosen, 0)
            oracle = classes(candidate_ids, after_mask)
            expected = len(oracle[signature(AUTOMATA[0], after_mask)])
            assert len(after_ids) == expected
            assert chosen in safe_probe_candidates(mask, safe_mask)
            rows.append({"mask": mask, "safe_mask": safe_mask, "chosen": chosen,
                         "before": len(candidate_ids), "after": len(after_ids),
                         "preserves_unknown": len(after_ids) > 1})
    assert all(r["chosen"] is None or r["chosen"] in safe_probe_candidates(r["mask"], r["safe_mask"]) for r in rows)
    assert any(r["chosen"] is None and r["before"] > 1 for r in rows)
    assert any(r["chosen"] is not None and r["after"] < r["before"] for r in rows)
    result = {"decision": "PASS_SAFE_PROBE_IDENTIFICATION_SCOPED", "automata": len(AUTOMATA),
              "masks": 1 << len(PAIRS), "safe_masks": 1 << len(PAIRS), "rows": len(rows),
              "unsafe_probe_admissions": 0, "deterministic_tie_break": "lowest_pair_index",
              "formal_invocations": 1, "reruns": 0, "replacements": 0, "tuning": 0,
              "sha256": hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
    return result

if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, indent=2))
