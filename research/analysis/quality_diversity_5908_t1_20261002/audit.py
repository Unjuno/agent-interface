"""Independent auditor replays chosen IDs and recomputes admissions, cells and labels."""
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).parent


def reference_ids(method, pool, limit, seeded_order):
    """Separate selector reconstruction, intentionally not imported from candidate."""
    todo = sorted(pool, key=lambda r:r["id"])
    chosen = []
    if method == "uniform-seeded":
        permitted={r["id"] for r in todo}
        return [cid for cid in seeded_order if cid in permitted][:limit]
    if method == "pairwise":
        seen = set()
        factors = ("motion","staleness","control")
        while todo and len(chosen) < limit:
            scored=[]
            for row in todo:
                f=row["features"]
                pairs={(a,f[a],b,f[b]) for a,b in itertools.combinations(factors,2)}
                scored.append((len(pairs-seen),row["id"],row))
            top=max(x[0] for x in scored)
            row=min((x[2] for x in scored if x[0]==top),key=lambda r:r["id"])
            f=row["features"]
            seen |= {(a,f[a],b,f[b]) for a,b in itertools.combinations(factors,2)}
            chosen.append(row); todo.remove(row)
        return [r["id"] for r in chosen]
    if method == "descriptor-archive":
        while todo and len(chosen) < limit:
            if not chosen:
                row=todo[0]
            else:
                distances={r["id"]:min(sum(r["features"][k]!=old["features"][k] for k in ("motion","staleness","control")) for old in chosen) for r in todo}
                farthest=max(distances.values())
                row=next(r for r in todo if distances[r["id"]]==farthest)
            chosen.append(row); todo.remove(row)
        return [r["id"] for r in chosen]
    raise ValueError(method)


def independently_expected(public, truth, recorded):
    cases = {x["id"]:x for x in public["cases"]}
    bad = {k:v["reason"] for k,v in truth["admission"].items() if not v["admit"]}
    good = {k for k,v in truth["admission"].items() if v["admit"]}
    pool = [{"id":c["id"],"features":c["features"]} for c in public["cases"] if c["id"] in good]
    out = {"rejected_before_call":bad,"policies":{},"errors":[]}
    for method, result in recorded["policies"].items():
        ids = result["selected_case_ids"]
        if ids != reference_ids(method,pool,public["budget"],public["uniform_seeded_order"]):
            out["errors"].append(method+":selector_sequence_mismatch")
        if len(ids) != public["budget"] or len(set(ids)) != len(ids):
            out["errors"].append(method+":call_count_or_duplicate")
        if any(i not in good for i in ids):
            out["errors"].append(method+":inadmissible_case_selected")
        # Recompute every label/cell from the separate truth map; do not import candidate.
        bins, mechanisms, rows = {}, set(), []
        for n, cid in enumerate(ids, 1):
            if cid not in truth["evaluation"]:
                out["errors"].append(method+":no_eligible_evaluation_for_selected_case")
                continue
            ev = truth["evaluation"][cid]
            trace = ev["trace"]
            label = ev["mechanism"]
            key = "|".join((trace["phase"], trace["local_state"], trace["event"]))
            bins.setdefault(key, {"first_case":cid,"members":[]})["members"].append(cid)
            if label:
                mechanisms.add(label)
            rows.append({"call":n,"case_id":cid,"visible_features":cases[cid]["features"],"observed_trace":trace,"adjudication_label":label})
        if result["rows"] != rows or result["trace_archive"] != bins:
            out["errors"].append(method+":raw_reconstruction_mismatch")
        out["policies"][method] = {"call_count":len(ids),"unique_mechanisms":sorted(mechanisms),"trace_cells":len(bins),"selected_case_ids":ids}
    leaked = recorded.get("audit_boundary",{}).get("selector_received_truth") is not False or recorded.get("audit_boundary",{}).get("selector_received_traces_for_unevaluated_cases") is not False
    if leaked:
        out["errors"].append("selector_boundary_leak")
    qd=out["policies"].get("descriptor-archive",{})
    qd_mechanism_cells={}
    for cid in qd.get("selected_case_ids",[]):
        if cid not in truth["evaluation"]:
            continue
        ev=truth["evaluation"][cid]
        if ev["mechanism"]:
            t=ev["trace"]; cell="|".join((t["phase"],t["local_state"],t["event"]))
            qd_mechanism_cells.setdefault(ev["mechanism"],set()).add(cell)
    distinct_cells=len(qd_mechanism_cells)==2 and all(len(cells)==1 for cells in qd_mechanism_cells.values()) and len(set.union(*qd_mechanism_cells.values()))==2 if qd_mechanism_cells else False
    return {"schema":"agent-interface.quality-diversity-5908.audit.v1","enumerated_cases":len(cases),"admitted_cases":len(good),"rejected_cases":bad,"policies":out["policies"],"distinct_mechanism_cells":distinct_cells,"errors":out["errors"],"status":"METHOD_PASS_SCOPED" if not out["errors"] and len(qd.get("unique_mechanisms",[]))==2 and distinct_cells else "FAIL_OR_HOLD"}


if __name__ == "__main__":
    pub = json.loads((ROOT/"public.json").read_text())
    truth = json.loads((ROOT/"truth.json").read_text())
    candidate = json.loads((ROOT/"results/formal-01/candidate.stdout").read_text())
    print(json.dumps(independently_expected(pub,truth,candidate),sort_keys=True,separators=(",",":")))
