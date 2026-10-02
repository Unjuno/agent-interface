"""One-shot differential audit controls; no candidate code is run."""
import copy
import hashlib
import json
from pathlib import Path

import audit_v2
import legacy_audit_exact

HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE / "fixture.json"
RAW_PATH = HERE / "reused_raw.json"
OUT_PATH = HERE / "differential_result.json"


def read_inputs():
    fb = FIXTURE_PATH.read_bytes()
    fixture = json.loads(fb)
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    return fixture, fb, raw


def control_decks(raw):
    semantic = {}
    def add(name, change):
        changed = copy.deepcopy(raw["rows"])
        change(changed)
        semantic[name] = changed
    add("threat_release", lambda r: r[0].__setitem__("threat_exec", None))
    add("active_deopt", lambda r: r[0]["active_arbitration"]["selected"].__setitem__("motor", {"proposal_id": "deopt-g1"}))
    add("score_missing", lambda r: r[0]["score"].pop("kill_count"))
    add("signal_missing", lambda r: r[0].__setitem__("final_health", None))
    add("traceback", lambda r: r[0].__setitem__("stderr", "Traceback (synthetic)"))
    add("baseline_stale_selection", lambda r: r[0]["post_handoff_arbitration"]["selected"]["locomotion"].__setitem__("proposal_id", "other"))
    add("baseline_release", lambda r: r[0]["stale_exec"]["terminal"]["release"].__setitem__("keys_down", ["w"]))
    add("candidate_stale_selected", lambda r: r[1]["post_handoff_arbitration"]["selected"].__setitem__("locomotion", {"proposal_id": "deopt-g1"}))
    add("candidate_stale_admission", lambda r: (r[1].__setitem__("stale_submit_count", 1), r[1].__setitem__("stale_exec", {"terminal": {"status": "completed", "release": {"verified": True, "keys_down": [], "buttons_down": []}}})))
    add("candidate_fresh_selection", lambda r: r[1]["fresh_arbitration"]["selected"]["locomotion"].__setitem__("proposal_id", "other"))
    add("candidate_fresh_release", lambda r: r[1]["fresh_exec"]["terminal"]["release"].__setitem__("verified", False))
    short = copy.deepcopy(raw["rows"][:-1])
    semantic["case_completeness"] = short

    identities = {}
    for field, value in (("id", "unknown-case"), ("pair", 99),
                         ("runtime_bundle_sha256", "0" * 64),
                         ("fixture_id", "other-fixture"), ("fixture_seed", 1)):
        changed = copy.deepcopy(raw["rows"])
        changed[0][field] = value
        identities[field] = changed
    return semantic, identities


def analyze():
    fixture, fb, raw = read_inputs()
    new_base = audit_v2.audit(raw, fixture, fb)
    old_base = legacy_audit_exact.audit(raw["rows"])
    semantics, identities = control_decks(raw)
    semantic_results = {}
    for name, rows in semantics.items():
        old = legacy_audit_exact.audit(rows)
        new_raw = {**raw, "rows": rows}
        new = audit_v2.audit(new_raw, fixture, fb)
        semantic_results[name] = {"legacy_rejected": bool(old["errors"]), "successor_rejected": bool(new["errors"])}
    identity_results = {}
    for field, rows in identities.items():
        old = legacy_audit_exact.audit(rows)
        new = audit_v2.audit({**raw, "rows": rows}, fixture, fb)
        identity_results[field] = {"legacy_accepted": not bool(old["errors"]), "successor_rejected": bool(new["errors"])}
    passed = (not new_base["errors"] and not old_base["errors"]
              and all(v["legacy_rejected"] and v["successor_rejected"] for v in semantic_results.values())
              and all(v["legacy_accepted"] and v["successor_rejected"] for v in identity_results.values()))
    return {
        "decision": "PASS_AUDITOR_SEMANTIC_COMPATIBILITY_AND_IDENTITY_SCOPED" if passed else "FAIL_AUDITOR_SEMANTIC_COMPATIBILITY_AND_IDENTITY_SCOPED",
        "exact_legacy_source_sha256": hashlib.sha256((HERE / "legacy_audit_exact.py").read_bytes()).hexdigest(),
        "reused_raw_sha256": hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(),
        "fixture_sha256": hashlib.sha256(fb).hexdigest(),
        "legacy_baseline": old_base,
        "successor_baseline": new_base,
        "semantic_controls": semantic_results,
        "identity_controls": identity_results,
        "candidate_invocations": 0,
        "formal_rows": 0,
    }


def main():
    if OUT_PATH.exists():
        raise SystemExit("STOP_OUTPUT_EXISTS")
    result = analyze()
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["decision"] != "PASS_AUDITOR_SEMANTIC_COMPATIBILITY_AND_IDENTITY_SCOPED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
