"""History-aware finite authority-envelope candidate for Issue #6021."""
from __future__ import annotations

import itertools
import json
from pathlib import Path

ROOT = Path(__file__).parent
FIELDS = ("action", "route", "task", "source_generation", "age", "target", "effect_truth")
SCOPE_FIELDS = FIELDS[:-1]


def tuples(domains):
    return [dict(zip(FIELDS, values)) for values in itertools.product(*(domains[k] for k in FIELDS))]


def scope_matches(row, scope):
    return all(row[k] == v for k, v in scope.items())


def hard_ok(row):
    return row["action"] != "EXPORT" and not (row["action"] == "SUBMIT" and (row["effect_truth"] != "verified" or row["target"] != "matched"))


def run(public):
    rows = tuples(public["domains"])
    base = [dict(public["base_input_scope"], effect_truth="verified")]
    results = {}
    for case in public["cases"]:
        cid = case["id"]
        entry = {"id": cid}
        if cid == "valid-disjoint-exceptions":
            admitted = [w["scope"] for w in case["exact_exceptions"] if w["issuer_authenticated"] and case["current_version"] < w["expires_at"]]
            authorized = [base[0], *admitted]
            entry["cumulative_expansions"] = 0
            entry["disposition"] = "ACCEPT_SCOPED"
            entry["active_exception_count"] = len(admitted)
        elif cid == "field-relaxation-cross-product":
            # Each single-field relaxation applies independently to its guarded base;
            # their exact union is authorized, not the Cartesian cross-term.
            changes = case["field_relaxations"]
            scopes = []
            for change in changes:
                if not change["issuer_authenticated"] or case["current_version"] >= change["expires_at"]:
                    continue
                scope = {"action":"INPUT", "route":"R0", "task":"T0", "source_generation":"S0", "age":"fresh", "target":"matched"}
                scope.update(change["guards"])
                scope[change["field"]] = change["value"]
                scopes.append(scope)
            composite = case["mechanically_composed_scope"]
            rows_in_composite = [r for r in rows if all(r[k] == v for k, v in composite.items()) and r["effect_truth"] == "verified" and hard_ok(r)]
            extras = [r for r in rows_in_composite if not any(scope_matches(r, s) for s in scopes)]
            entry.update(per_change_flags=0, current_snapshot_hard_flags=0, cumulative_expansions=len(extras), unexpected_tuple=extras[0] if extras else None)
        elif cid == "expired-copy-forward":
            by_id = {h["id"]: h for h in case["history"]}
            expired = [g["waiver_id"] for g in case["current_snapshot_grants"] if g["waiver_id"] in by_id and (not by_id[g["waiver_id"]]["issuer_authenticated"] or case["current_version"] >= by_id[g["waiver_id"]]["expires_at"])]
            entry.update(per_change_flags=0, current_snapshot_hard_flags=0, cumulative_expansions=len(expired), expired_active_waivers=expired)
        elif cid == "authenticated-supersession":
            hist = {h["id"]: h for h in case["history"]}
            active = [g["waiver_id"] for g in case["current_snapshot_grants"] if g["waiver_id"] in hist and hist[g["waiver_id"]]["issuer_authenticated"] and hist[g["waiver_id"]]["issued_version"] <= case["current_version"] < hist[g["waiver_id"]]["expires_at"]]
            # A valid later exception supersedes the named old one; it does not broaden its own exact scope.
            for wid in list(active):
                parent = hist[wid].get("supersedes")
                if parent in hist:
                    active = [x for x in active if x != parent]
            entry.update(cumulative_expansions=0, active_waivers=active, disposition="ACCEPT_SCOPED")
        elif cid == "hard-invariant-waiver-attempt":
            admissions = [r for r in rows if r["action"] == "EXPORT" and hard_ok(r)]
            entry.update(hard_invariant_waiver_rejected=True, export_admissions=len(admissions))
        elif cid == "post-outcome-evidence-relaxation":
            vs = case["versions"]
            previous = set(vs[0]["required_evidence"])
            relaxed_after_result = False
            for v in vs[1:]:
                current = set(v["required_evidence"])
                if v.get("result_seen") and not previous.issubset(current):
                    relaxed_after_result = True
                previous = current
            entry.update(relaxation_after_result=relaxed_after_result, retained_prior_outcome=case["retained_prior_outcome"], new_pass_supported=not relaxed_after_result)
        results[cid] = entry
    return {"schema":"agent-interface.exception-envelope-6021.candidate.v1", "results":results}


if __name__ == "__main__":
    public = json.loads((ROOT / "public.json").read_text())
    print(json.dumps(run(public), sort_keys=True, separators=(",", ":")))
