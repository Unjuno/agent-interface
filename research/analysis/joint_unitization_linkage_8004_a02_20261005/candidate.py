"""Candidate-only finite enumerator; deliberately has no oracle input."""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path


def _components(observations, segmentation, links):
    records = {r["record_id"]: r for r in observations["raw_records"]}
    unit_of = {}
    units = {}
    for channel in observations["channels"]:
        groups = segmentation[channel]
        for ix, group in enumerate(groups):
            uid = f"{channel}:{ix}"
            units[uid] = {"channel": channel, "records": list(group)}
            for record_id in group:
                if record_id not in records or records[record_id]["channel"] != channel or record_id in unit_of:
                    raise ValueError("invalid segmentation partition")
                unit_of[record_id] = uid
    if set(unit_of) != set(records):
        raise ValueError("segmentation does not cover raw records exactly once")

    parent = {uid: uid for uid in units}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for left, right in links:
        if left not in unit_of or right not in unit_of:
            raise ValueError("link references unknown record")
        if records[left]["channel"] == records[right]["channel"]:
            raise ValueError("cross-channel link required")
        a, b = find(unit_of[left]), find(unit_of[right])
        if a != b:
            parent[b] = a
    groups = {}
    for uid, unit in units.items():
        groups.setdefault(find(uid), []).extend(unit["records"])
    comps = []
    channel_order = observations["channels"]
    for recs in groups.values():
        recs = sorted(recs)
        seen = {records[r]["channel"] for r in recs}
        vector = "".join("1" if c in seen else "0" for c in channel_order)
        comps.append({"records": recs, "capture_vector": vector})
    return sorted(comps, key=lambda x: (x["capture_vector"], x["records"]))


def evaluate(observations):
    rows = []
    for (s_name, segmentation), (l_name, links) in product(
        observations["segmentation_alternatives"].items(),
        observations["linkage_alternatives"].items(),
    ):
        comps = _components(observations, segmentation, links)
        rows.append({
            "assignment": f"{s_name}+{l_name}",
            "segmentation": s_name,
            "linkage": l_name,
            "components": comps,
            "component_count": len(comps),
            "capture_histogram": {v: sum(c["capture_vector"] == v for c in comps) for v in sorted({c["capture_vector"] for c in comps})},
            "links": [list(e) for e in links],
        })
    signatures = {(r["component_count"], json.dumps(r["capture_histogram"], sort_keys=True)) for r in rows}
    return {
        "channels": list(observations["channels"]),
        "assignment_count": len(rows),
        "assignments": rows,
        "disposition": "UNIDENTIFIED" if len(signatures) > 1 else "STABLE_WITHIN_AUTHORED_SET",
    }


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--observations", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    result = evaluate(json.loads(Path(a.observations).read_text()))
    Path(a.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"assignments": result["assignment_count"], "disposition": result["disposition"]}, sort_keys=True))
