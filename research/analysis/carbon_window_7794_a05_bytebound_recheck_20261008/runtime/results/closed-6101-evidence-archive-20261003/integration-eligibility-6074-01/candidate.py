import json
from pathlib import Path

CASES = Path(__file__).with_name("cases.json")

def classify(case):
    if case["coverage"] != "complete" or case["identity"] != "bound":
        return "UNKNOWN"
    if case["predicate"] == "ordered_timestamps":
        a, b = case["timestamp_a"], case["timestamp_b"]
        if a[1] < b[0]: return "ROBUST_TRUE_SCOPED"
        if a[0] > b[1]: return "ROBUST_FALSE_SCOPED"
        return "UNKNOWN"
    lo, hi = case["value_interval"]
    threshold = 12 if case["predicate"] == "distance_le_12" else 100
    if hi < threshold: return "ROBUST_TRUE_SCOPED"
    if lo > threshold: return "ROBUST_FALSE_SCOPED"
    return "UNKNOWN"

def main():
    data=json.loads(CASES.read_text(encoding="utf-8"))
    rows=[]
    for c in data["cases"]:
        got=classify(c)
        rows.append({"id":c["id"],"nominal":c["nominal"],"expected":c["expected"],"actual":got,"match":got==c["expected"]})
    print(json.dumps({"schema":"issue-6074-t0-candidate-v1","rows":rows,"all_match":all(r["match"] for r in rows)},indent=2))
if __name__ == "__main__": main()
