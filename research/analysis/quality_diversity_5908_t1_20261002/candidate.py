"""Three equal-budget selectors plus a post-evaluation trace-cell archive."""
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).parent
FACTORS = ("motion", "staleness", "control")


def blind_selector(policy, pool, budget, seeded_order):
    """Only IDs/features enter this function; truth and trace are out of scope."""
    remaining = list(sorted(pool, key=lambda row: row["id"]))
    chosen = []
    if policy == "uniform-seeded":
        by_id={x["id"]:x for x in remaining}
        return [by_id[cid] for cid in seeded_order if cid in by_id][:budget]
    if policy == "pairwise":
        covered = set()
        while remaining and len(chosen) < budget:
            def gain(row):
                f = row["features"]
                pairs = {(a, f[a], b, f[b]) for a, b in itertools.combinations(FACTORS, 2)}
                return len(pairs - covered)
            row = max(remaining, key=lambda x: (gain(x), tuple(-ord(c) for c in x["id"])))
            chosen.append(row)
            f = row["features"]
            covered |= {(a, f[a], b, f[b]) for a, b in itertools.combinations(FACTORS, 2)}
            remaining.remove(row)
        return chosen
    if policy == "descriptor-archive":
        # Explore far from prior evaluated input-feature points. Trace descriptors
        # are added to the archive only after each call; they never score an
        # unevaluated case. Ties are deterministic by ID.
        while remaining and len(chosen) < budget:
            if not chosen:
                row = remaining[0]
            else:
                def novelty(row):
                    return min(sum(row["features"][k] != prior["features"][k] for k in FACTORS) for prior in chosen)
                best = max(novelty(row) for row in remaining)
                row = next(x for x in remaining if novelty(x) == best)
            chosen.append(row)
            remaining.remove(row)
        return chosen
    raise ValueError(policy)


def trace_cell(trace):
    return (trace["phase"], trace["local_state"], trace["event"])


def run(public, truth):
    rejected = {case["id"]: truth["admission"][case["id"]]["reason"] for case in public["cases"] if not truth["admission"][case["id"]]["admit"]}
    # The independent admission oracle forms a pre-evaluation legal pool. The
    # selector receives only candidate IDs and authored visible features.
    pool = [{"id": c["id"], "features": c["features"]} for c in public["cases"] if truth["admission"][c["id"]]["admit"]]
    output = {"schema":"agent-interface.quality-diversity-5908.candidate.v1", "budget":public["budget"], "rejected_before_call":rejected, "policies":{}}
    for policy in ("uniform-seeded", "pairwise", "descriptor-archive"):
        selected = blind_selector(policy, pool, public["budget"], public["uniform_seeded_order"])
        rows = []
        cells = {}
        for index, case in enumerate(selected, 1):
            observed = truth["evaluation"][case["id"]]
            cell = trace_cell(observed["trace"])
            cells.setdefault("|".join(cell), {"first_case":case["id"], "members":[]})["members"].append(case["id"])
            rows.append({"call":index,"case_id":case["id"],"visible_features":case["features"],"observed_trace":observed["trace"],"adjudication_label":observed["mechanism"]})
        output["policies"][policy] = {"selected_case_ids":[x["id"] for x in selected],"rows":rows,"trace_archive":cells,"unique_mechanisms":sorted({r["adjudication_label"] for r in rows if r["adjudication_label"]}),"call_count":len(rows)}
    output["audit_boundary"] = {"selector_input_keys":["id","features"],"selector_received_truth":False,"selector_received_traces_for_unevaluated_cases":False}
    return output


if __name__ == "__main__":
    public = json.loads((ROOT/"public.json").read_text())
    truth = json.loads((ROOT/"truth.json").read_text())
    print(json.dumps(run(public, truth), sort_keys=True, separators=(",",":")))
