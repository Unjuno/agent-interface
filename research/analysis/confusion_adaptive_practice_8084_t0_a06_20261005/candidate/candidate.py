"""Candidate: evaluate opaque diagnostic rows under a pre-frozen gate grid."""
import json


def execute(data):
    rows = []
    for row in data["rows"]:
        rates = [x / row["n"] for x in row["successes"]]
        span = max(rates) - min(rates)
        peak = max(rates)
        mask = 0
        bit = 0
        for minimum_span in data["span_grid"]:
            for minimum_peak in data["peak_grid"]:
                if span >= minimum_span and peak >= minimum_peak:
                    mask |= 1 << bit
                bit += 1
        rows.append({"row_id": row["row_id"], "gate_mask": mask})
    return {"schema": "issue8084-a06-candidate-v1", "rows": rows}


if __name__ == "__main__":
    with open("observed_counts.json", encoding="utf-8") as f:
        data = json.load(f)
    print(json.dumps(execute(data), sort_keys=True, separators=(",", ":")))
