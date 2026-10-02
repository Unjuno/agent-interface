"""Independent finite endpoint oracle; intentionally does not import candidate.py."""
import itertools, json
from pathlib import Path

cases=json.loads(Path(__file__).with_name("cases.json").read_text(encoding="utf-8"))["cases"]
def endpoint_result(c):
    if c["coverage"]!="complete" or c["identity"]!="bound": return "UNKNOWN"
    if c["predicate"]=="ordered_timestamps":
        margins={y-x for x,y in itertools.product(c["timestamp_a"],c["timestamp_b"])}
        return "ROBUST_TRUE_SCOPED" if min(margins)>0 else "ROBUST_FALSE_SCOPED" if max(margins)<0 else "UNKNOWN"
    threshold=12 if c["predicate"]=="distance_le_12" else 100
    if c["predicate"] not in ("distance_le_12","latency_le_100"): return "UNKNOWN"
    margins={threshold-x for x in c["value_interval"]}
    return "ROBUST_TRUE_SCOPED" if min(margins)>0 else "ROBUST_FALSE_SCOPED" if max(margins)<0 else "UNKNOWN"
rows=[{"id":c["id"],"expected":c["expected"],"oracle":endpoint_result(c),"match":endpoint_result(c)==c["expected"]} for c in cases]
print(json.dumps({"schema":"issue-6074-t0-independent-oracle-v1","rows":rows,"all_match":all(r["match"] for r in rows)},indent=2))
