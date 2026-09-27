from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path


PASS = "PASS_XSERVER_LIFETIME_BINDING_REQUIRED_SCOPED"


def typed_oracle(receipt: dict, current: dict) -> tuple[str, str]:
    if receipt.get("authority") != "none":
        return "INVALID", "authority_not_none"
    if receipt.get("task_input_granted") is not False:
        return "INVALID", "task_input_not_false"
    if receipt.get("action_admission_eligible") is not False:
        return "INVALID", "action_admission_not_false"
    r = receipt.get("identity")
    if not isinstance(r, dict) or not isinstance(current, dict):
        return "INVALID", "identity_not_mapping"
    specs = {"backend": ("KNOWN", str), "top_level_client_id": ("KNOWN", int),
             "transient_for": (None, int)}
    for key, (required, value_type) in specs.items():
        a, b = r.get(key), current.get(key)
        if not isinstance(a, dict) or not isinstance(b, dict):
            return "INVALID", f"missing_evidence:{key}"
        for item in (a, b):
            state = item.get("state")
            if state not in {"KNOWN", "KNOWN_NULL", "UNKNOWN"}:
                return "INVALID", f"invalid_state:{key}"
            if required is not None and state != required:
                return "INVALID", f"required_known:{key}"
            if state == "KNOWN":
                if "value" not in item or type(item["value"]) not in (str, int):
                    return "INVALID", f"invalid_known_value:{key}"
                if value_type is not None and not isinstance(item["value"], value_type):
                    return "INVALID", f"invalid_value_type:{key}"
            elif "value" in item:
                return "INVALID", f"value_on_non_known:{key}"
        if key in ("backend", "top_level_client_id") and a.get("value") != b.get("value"):
            return "MISMATCH", f"core_mismatch:{key}"
    a, b = r["transient_for"], current["transient_for"]
    if "UNKNOWN" in (a["state"], b["state"]):
        return "CORE_MATCH_REFINEMENT_UNKNOWN", "core_match_transient_refinement_unknown"
    va = a.get("value") if a["state"] == "KNOWN" else None
    vb = b.get("value") if b["state"] == "KNOWN" else None
    if va != vb:
        return "MISMATCH", "refinement_mismatch:transient_for"
    return "EXACT_MATCH", "all_observed_identity_equal"


def row_disposition(row: dict, registry: dict) -> tuple[bool, str]:
    typed, reason = typed_oracle(row.get("receipt", {}), row.get("current_identity", {}))
    if row.get("typed", {}).get("classification") != typed:
        return False, "typed result differs from independent oracle"
    if row.get("typed", {}).get("reason") != reason:
        return False, "typed reason differs from independent oracle"
    case, policy = row.get("case"), row.get("policy")
    if policy == "CURRENT_TYPED":
        expected = "ACCEPT" if typed == "EXACT_MATCH" else "REJECT"
        if row.get("bound") != expected:
            return False, "current typed acceptance mismatch"
        return True, "ok"
    receipt = row.get("receipt", {})
    issued_token = registry.get(receipt.get("receipt_id"))
    if issued_token is None:
        expected, why = "REJECT", "unknown_receipt"
    elif receipt.get("server_instance_id") != issued_token:
        expected, why = "REJECT", "receipt_token_forged_or_changed"
    elif issued_token != row.get("server_instance_id"):
        expected, why = "REJECT", "server_instance_mismatch"
    else:
        expected = "ACCEPT" if typed == "EXACT_MATCH" else "REJECT"
        why = reason
    if row.get("bound") != expected:
        return False, "lifetime-bound acceptance mismatch"
    result = row.get("bound_result", {})
    if result.get("classification") != expected or result.get("reason") != why:
        return False, "lifetime-bound reason mismatch"
    return True, "ok"


def reconstruct(raw: dict) -> tuple[str, list[str]]:
    errors: list[str] = []
    rows, pairs = raw.get("rows"), raw.get("pairs")
    if not isinstance(rows, list) or len(rows) != 16:
        errors.append("expected exactly 16 rows")
        return "HOLD_OR_STOP_UNCLASSIFIED", errors
    if not isinstance(pairs, list) or len(pairs) != 4:
        errors.append("expected exactly 4 generation pairs")
        return "HOLD_OR_STOP_UNCLASSIFIED", errors
    expected_keys = {(rep, case, policy) for rep in range(4)
                     for case in ("same_generation", "cross_generation_stale")
                     for policy in ("CURRENT_TYPED", "LIFETIME_BOUND")}
    observed_keys = {(r.get("rep"), r.get("case"), r.get("policy")) for r in rows}
    if observed_keys != expected_keys:
        errors.append("row denominator/order keys differ from frozen matrix")
    pair_by_rep = {p.get("rep"): p for p in pairs}
    if set(pair_by_rep) != set(range(4)):
        errors.append("pair repetition IDs are not exactly 0..3")
    issued = raw.get("issued_receipts")
    if not isinstance(issued, list) or len(issued) != 8:
        errors.append("issued receipt ledger must contain exactly 8 entries")
        issued = []
    registry = {item.get("receipt_id"): item.get("server_instance_id") for item in issued
                if isinstance(item, dict)}
    if len(registry) != 8 or None in registry or len(set(registry)) != 8:
        errors.append("issued receipt ledger contains missing or duplicate IDs")
    structural_ok = True
    for pair in pairs:
        g1, g2 = pair.get("g1", {}), pair.get("g2", {})
        if g1.get("server_instance_id") == g2.get("server_instance_id"):
            errors.append(f"rep {pair.get('rep')}: lifetime token reused")
        if g1.get("xvfb_pid") == g2.get("xvfb_pid") or g1.get("xvfb_start_ticks") == g2.get("xvfb_start_ticks"):
            errors.append(f"rep {pair.get('rep')}: server process incarnation not distinct")
        for name, server in (("g1", g1), ("g2", g2)):
            if not server.get("socket_present_after_start"):
                errors.append(f"rep {pair.get('rep')} {name}: start socket missing")
        for phase in ("g1_cleanup", "g2_cleanup"):
            witness = pair.get(phase, {})
            if witness.get("exit_observed") is not True or witness.get("exit_code") != 0:
                errors.append(f"rep {pair.get('rep')} {phase}: Xvfb exit not clean")
            if witness.get("socket_disappeared") is not True:
                errors.append(f"rep {pair.get('rep')} {phase}: socket persisted")
        for key in ("same_xid", "same_root_xid", "core_identity_equal", "server_tokens_distinct"):
            if pair.get(key) is not True:
                errors.append(f"rep {pair.get('rep')}: {key} false")
        for gen in (g1, g2):
            ident = gen.get("identity", {})
            context = gen.get("context", {})
            if ident.get("backend") != {"state": "KNOWN", "value": "x11"}:
                errors.append("backend identity is not known X11")
            if ident.get("top_level_client_id", {}).get("value") != context.get("top_level_xid"):
                errors.append("typed client id does not match fixture XID")
            if ident.get("transient_for") != {"state": "KNOWN_NULL"}:
                errors.append("transient absence was not observed as KNOWN_NULL")
            if context.get("wm_name") != "typed-recovery-lifetime":
                errors.append("fixture WM name mismatch")
        if g1.get("identity_reread_top_level_xid") != g1.get("context", {}).get("top_level_xid"):
            errors.append("same-generation re-read did not query same top-level XID")
        if g1.get("same_generation_requery_equal") is not True:
            errors.append("same-generation re-read identity mismatch")
    for row in rows:
        receipt = row.get("receipt", {})
        rid = receipt.get("receipt_id")
        if rid not in registry:
            errors.append("row receipt absent from independently checked issued ledger")
        if receipt.get("authority") != "none" or receipt.get("task_input_granted") is not False or receipt.get("action_admission_eligible") is not False:
            errors.append("recovery receipt is not observation-only")
        ok, why = row_disposition(row, registry)
        if not ok:
            errors.append(f"rep {row.get('rep')} {row.get('case')} {row.get('policy')}: {why}")
    if raw.get("formal_invocations") != 1 or raw.get("reruns") != 0:
        errors.append("formal invocation/retry count mismatch")
    if raw.get("authority") != 0 or raw.get("input_calls") != 0:
        errors.append("nonzero authority or task input")
    controls = raw.get("negative_controls")
    expected_controls = {"forged_server_token": "REJECT", "missing_server_token": "REJECT",
                         "unknown_receipt_id": "REJECT", "authority_escalation": "INVALID",
                         "changed_backend": "MISMATCH", "changed_client_id": "MISMATCH",
                         "known_transient_mismatch": "MISMATCH"}
    if not isinstance(controls, list) or len(controls) != 28:
        errors.append("negative controls missing or failed")
    else:
        for rep in range(4):
            these = [c for c in controls if c.get("rep") == rep]
            if len(these) != 7 or {c.get("name") for c in these} != set(expected_controls):
                errors.append(f"rep {rep}: negative-control denominator mismatch")
            for control in these:
                expected = expected_controls.get(control.get("name"))
                if (control.get("expected") != expected
                        or control.get("observed", {}).get("classification") != expected
                        or control.get("detected") is not True):
                    errors.append(f"rep {rep}: negative control did not fail closed: {control.get('name')}")
    if errors:
        return "STOP_OR_HOLD_AUDIT", errors
    same_rows = [r for r in rows if r.get("case") == "same_generation"]
    cross_rows = [r for r in rows if r.get("case") == "cross_generation_stale"]
    if any(not p.get("core_identity_equal") or not p.get("same_xid") for p in pairs):
        decision = "HOLD_NO_XID_REUSE_DISCRIMINATOR"
    elif any(r.get("policy") == "LIFETIME_BOUND" and r.get("bound") == "ACCEPT" for r in cross_rows):
        decision = "FAIL_LIFETIME_ESCAPE"
    elif any(r.get("policy") == "LIFETIME_BOUND" and r.get("bound") != "ACCEPT" for r in same_rows):
        decision = "FAIL_LIFETIME_OVERINVALIDATION"
    elif (all(r.get("typed", {}).get("classification") == "EXACT_MATCH" for r in same_rows)
          and all(r.get("typed", {}).get("classification") == "EXACT_MATCH" for r in cross_rows)
          and all(r.get("policy") == "LIFETIME_BOUND" and r.get("bound") == "REJECT"
                  for r in cross_rows if r.get("policy") == "LIFETIME_BOUND")
          and all(r.get("policy") == "LIFETIME_BOUND" and r.get("bound") == "ACCEPT"
                  for r in same_rows if r.get("policy") == "LIFETIME_BOUND")):
        decision = PASS
    else:
        decision = "HOLD_OR_STOP_UNCLASSIFIED"
    if raw.get("decision") != decision:
        return "STOP_OR_HOLD_AUDIT", [f"runner decision {raw.get('decision')} != independent decision {decision}"]
    return decision, []


def controls_pass(raw: dict) -> list[dict]:
    checks = []
    base, _ = reconstruct(raw)
    mutations = [
        ("row-dropped", lambda x: x["rows"].pop()),
        ("row-duplicated", lambda x: x["rows"].append(copy.deepcopy(x["rows"][0]))),
        ("xid-mutated", lambda x: x["pairs"][0]["g2"]["identity"]["top_level_client_id"].update(value=4)),
        ("same-token", lambda x: x["pairs"][0]["g2"].update(server_instance_id=x["pairs"][0]["g1"]["server_instance_id"])),
        ("authority-escalated", lambda x: x["rows"][0]["receipt"].update(authority="task-input")),
        ("release/socket-lifecycle-missing", lambda x: x["pairs"][0]["g1_cleanup"].update(socket_disappeared=False)),
        ("false-pass-decision", lambda x: x.update(decision="PASS_XSERVER_LIFETIME_BINDING_REQUIRED_SCOPED")),
    ]
    for name, mutate in mutations:
        changed = copy.deepcopy(raw)
        mutate(changed)
        disposition, _ = reconstruct(changed)
        detected = disposition != base
        if name == "false-pass-decision":
            detected = (changed.get("decision") == PASS and disposition != PASS)
        checks.append({"name": name, "detected": detected, "mutated_disposition": disposition})
    return checks


def main() -> None:
    root = Path("/evidence")
    raw_bytes = (root / "raw.json").read_bytes()
    raw = json.loads(raw_bytes)
    freeze_bytes = Path("/freeze.json").read_bytes()
    source_bytes = Path("/source_manifest.json").read_bytes()
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    source_sha = hashlib.sha256(source_bytes).hexdigest()
    errors = []
    if raw.get("freeze_sha256") != freeze_sha:
        errors.append("raw/freeze SHA-256 mismatch")
    if raw.get("source_manifest_sha256") != source_sha:
        errors.append("raw/source-manifest SHA-256 mismatch")
    disposition, reconstruction_errors = reconstruct(raw)
    errors.extend(reconstruction_errors)
    mutations = controls_pass(raw)
    if not all(x["detected"] for x in mutations):
        errors.append("auditor corruption control failed")
    final = disposition if not errors else "STOP_OR_HOLD_AUDIT"
    audit = {
        "audit": "PASS_INDEPENDENT_LIFETIME_AUDIT" if final == PASS else "STOP_OR_HOLD_AUDIT",
        "candidate_decision": raw.get("decision"),
        "independent_decision": final,
        "raw_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "freeze_sha256": freeze_sha,
        "source_manifest_sha256": source_sha,
        "reconstruction_errors": errors,
        "corruption_controls": mutations,
        "row_count": len(raw.get("rows", [])),
        "pair_count": len(raw.get("pairs", [])),
        "negative_control_count": len(raw.get("negative_controls", [])),
    }
    (root / "audit.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))
    if final not in {PASS, "FAIL_LIFETIME_ESCAPE", "FAIL_LIFETIME_OVERINVALIDATION", "HOLD_NO_XID_REUSE_DISCRIMINATOR"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
