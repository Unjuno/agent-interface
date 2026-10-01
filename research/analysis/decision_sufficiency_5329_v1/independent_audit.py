"""Independent raw-only finite-oracle audit; imports no analyze.py code."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NEEDS = {
    "OUTCOME_REDUCER": ("outcome",),
    "FRESHNESS_AUDITOR": ("fresh",),
    "EFFECT_ATTRIBUTION": ("fresh", "effect_link", "lineage"),
    "AUTHORITY_ADMISSION": ("fresh", "lineage", "authority", "protocol"),
    "CAUSAL_ATTRIBUTION": ("fresh", "effect_link", "lineage", "causal"),
    "RELEASE_GATE": ("outcome", "fresh", "lineage", "authority", "protocol"),
}
ARMS = ("LABEL_ONLY", "RAW_TRACE", "FIXED_SUMMARY", "DECISION_SUFFICIENT", "ADVERSARIAL_COMPRESSION")


def oracle(consumer: str, e: dict) -> str:
    needed = NEEDS[consumer]
    if any(k not in e for k in needed) or any(e[k] is None or e[k] == "UNKNOWN" for k in needed):
        return "UNKNOWN"
    if consumer == "OUTCOME_REDUCER":
        return e["outcome"]
    if consumer == "FRESHNESS_AUDITOR":
        return "FRESH" if e["fresh"] is True else "STALE"
    if consumer == "EFFECT_ATTRIBUTION":
        return "VERIFIED" if e["fresh"] is True and e["effect_link"] is True and e["lineage"] is True else "NOT_VERIFIED"
    if consumer == "AUTHORITY_ADMISSION":
        return "ADMIT" if e["fresh"] is True and e["lineage"] is True and e["authority"] is True and e["protocol"] == "OK" else "DENY"
    if consumer == "CAUSAL_ATTRIBUTION":
        return "SUPPORTED" if e["fresh"] is True and e["effect_link"] is True and e["lineage"] is True and e["causal"] == "SUPPORTED" else "NOT_SUPPORTED"
    if consumer == "RELEASE_GATE":
        if e["outcome"] == "FAIL":
            return "FAIL"
        return "PASS" if e["outcome"] == "PASS" and e["fresh"] is True and e["lineage"] is True and e["authority"] is True and e["protocol"] == "OK" else "HOLD"
    raise AssertionError(consumer)


def check(raw: dict, traces: list[dict]) -> list[str]:
    errors = []
    idx = {(r.get("trace"), r.get("consumer"), r.get("policy")): r for r in raw.get("rows", [])}
    wanted = {(t["id"], c, p) for t in traces for c in NEEDS for p in ARMS}
    if len(raw.get("rows", [])) != len(wanted) or set(idx) != wanted:
        errors.append("row_identity_or_count")
    for t in traces:
        for c, req in NEEDS.items():
            ref = oracle(c, t)
            for p in ARMS:
                r = idx.get((t["id"], c, p))
                if r is None:
                    continue
                if p == "LABEL_ONLY":
                    summary = {"outcome": t["outcome"], "raw_digest": t["raw_digest"]}
                    got = t["outcome"] if c == "RELEASE_GATE" else oracle(c, summary)
                elif p == "RAW_TRACE":
                    got = oracle(c, t)
                else:
                    fields = list(("outcome", "fresh", "effect_link") if p in ("FIXED_SUMMARY", "ADVERSARIAL_COMPRESSION") else req)
                    if p == "ADVERSARIAL_COMPRESSION":
                        candidates = sorted(set(req).intersection(fields))
                        if candidates:
                            fields.remove(candidates[0])
                    summary = {k: t[k] for k in fields if k in t}
                    got = oracle(c, summary)
                encoded = ({"outcome": t["outcome"], "raw_digest": t["raw_digest"]} if p == "LABEL_ONLY" else
                           t if p == "RAW_TRACE" else
                           {**{k: t[k] for k in fields if k in t}, "raw_digest": t["raw_digest"]})
                expected_fields = sorted(k for k in encoded if k != "raw_digest")
                should = {
                    "reference": ref, "decision": got, "equivalent": got == ref,
                    "unsafe_pass": c == "RELEASE_GATE" and got == "PASS" and ref != "PASS",
                    "unknown": got == "UNKNOWN",
                    "bytes": len(json.dumps(encoded, sort_keys=True, separators=(",", ":")).encode("utf-8")),
                    "fields": expected_fields,
                }
                for f, v in should.items():
                    if r.get(f) != v:
                        errors.append(f"{t['id']}:{c}:{p}:{f}")
    expected_summary = {}
    for p in ARMS:
        rows = [r for r in raw.get("rows", []) if r.get("policy") == p]
        expected_summary[p] = {
            "rows": len(rows), "decision_mismatches": sum(not r.get("equivalent") for r in rows),
            "unsafe_passes": sum(bool(r.get("unsafe_pass")) for r in rows),
            "unknowns": sum(bool(r.get("unknown")) for r in rows), "bytes": sum(r.get("bytes", 0) for r in rows),
        }
    if raw.get("summary") != expected_summary:
        errors.append("summary_mismatch")
    return errors


def run(raw_path: Path) -> dict:
    traces = json.loads((ROOT / "traces.json").read_text(encoding="utf-8"))["traces"]
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    controls = []
    changes = (
        ("drop_row", lambda x: x["rows"].pop()),
        ("force_release_pass", lambda x: x["rows"][2].update(decision="PASS")),
        ("corrupt_bytes", lambda x: x["rows"][0].update(bytes=-1)),
        ("erase_required_field", lambda x: x["rows"][20].update(fields=[])),
    )
    for name, fn in changes:
        changed = copy.deepcopy(raw)
        fn(changed)
        controls.append({"name": name, "rejected": bool(check(changed, traces))})
    errors = check(raw, traces)
    stats = raw.get("summary", {})
    pass_gate = (
        stats.get("DECISION_SUFFICIENT", {}).get("decision_mismatches") == 0
        and stats.get("DECISION_SUFFICIENT", {}).get("bytes", 10**9) < stats.get("RAW_TRACE", {}).get("bytes", 0)
        and stats.get("LABEL_ONLY", {}).get("unsafe_passes", 0) > 0
        and stats.get("ADVERSARIAL_COMPRESSION", {}).get("decision_mismatches", 0) > 0
        and all(x["rejected"] for x in controls)
    )
    return {"audit": "issue_5329_independent_exact_oracle_v1", "row_count": len(raw.get("rows", [])),
            "errors": errors, "controls": controls, "all_controls_rejected": all(x["rejected"] for x in controls),
            "analytic_gate": "PASS_FINITE_CONTRACT_ONLY" if pass_gate and not errors else "FAIL_OR_UNCERTAIN",
            "summary": stats}


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1])), sort_keys=True, indent=2))
