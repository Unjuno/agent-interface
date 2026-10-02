"""Independent raw-only contract auditor for the synthetic #626 successor."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE_PATH = HERE / "fixture.json"
RAW_PATH = HERE / "candidate_raw.json"
OUT_PATH = HERE / "audit_result.json"


def release_ok(value):
    if not isinstance(value, dict):
        return False
    terminal = value.get("terminal")
    if not isinstance(terminal, dict):
        return False
    release = terminal.get("release")
    return (terminal.get("status") == "completed" and isinstance(release, dict)
            and release.get("verified") is True and release.get("keys_down") == []
            and release.get("buttons_down") == [])


def audit(raw, fixture, fixture_bytes):
    errors = []
    rows = raw.get("rows") if isinstance(raw, dict) else None
    if not isinstance(raw, dict) or raw.get("schema") != "map01-threat-deopt-626-audit-identity-raw-v1":
        errors.append("raw_schema")
    if not isinstance(rows, list) or len(rows) != len(fixture["cases"]):
        errors.append("case_completeness")
        rows = rows if isinstance(rows, list) else []
    if raw.get("fixture_sha256") != hashlib.sha256(fixture_bytes).hexdigest():
        errors.append("fixture_digest")
    expected = fixture["cases"]
    if len(rows) == len(expected):
        for index, (row, case) in enumerate(zip(rows, expected)):
            if not isinstance(row, dict):
                errors.append(f"row_{index}:type")
                continue
            for key in ("id", "pair", "arm"):
                if row.get(key) != case[key]:
                    errors.append(f"row_{index}:identity_{key}")
            for key, value in (("runtime_bundle_sha256", fixture["runtime_bundle_sha256"]),
                               ("fixture_id", fixture["fixture_id"]),
                               ("fixture_seed", fixture["seed"])):
                if row.get(key) != value:
                    errors.append(f"row_{index}:identity_{key}")
    ids = [r.get("id") for r in rows if isinstance(r, dict)]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_case_id")

    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("id", "unknown"))
        active = row.get("active_arbitration")
        post = row.get("post_handoff_arbitration")
        if not isinstance(active, dict) or active.get("selected", {}).get("locomotion", {}).get("proposal_id") != "threat-g1":
            errors.append(name + ":active_threat")
        selected_active = active.get("selected", {}) if isinstance(active, dict) else {}
        if isinstance(selected_active, dict) and any(isinstance(v, dict) and v.get("proposal_id") == "deopt-g1" for v in selected_active.values()):
            errors.append(name + ":active_deopt")
        if not release_ok(row.get("threat_exec")):
            errors.append(name + ":threat_release")
        score = row.get("score")
        if not isinstance(score, dict) or any(k not in score or score[k] is None for k in ("kill_count", "death_count", "map_exit", "player_dead")):
            errors.append(name + ":score")
        if row.get("final_health") is None or row.get("final_ammo") is None:
            errors.append(name + ":signals")
        if not isinstance(row.get("stderr"), str) or "Traceback" in row.get("stderr", ""):
            errors.append(name + ":stderr")
        if row.get("arm") == "baseline":
            if not isinstance(post, dict) or post.get("selected", {}).get("locomotion", {}).get("proposal_id") != "deopt-g1":
                errors.append(name + ":baseline_stale_selection")
            if row.get("stale_submit_count") != 1 or not release_ok(row.get("stale_exec")):
                errors.append(name + ":baseline_stale_execution")
            if row.get("fresh_exec") is not None:
                errors.append(name + ":baseline_fresh_execution")
        elif row.get("arm") == "candidate":
            post_selected = post.get("selected", {}) if isinstance(post, dict) else {}
            deferred = post.get("deferred", []) if isinstance(post, dict) else []
            if not isinstance(post_selected, dict) or "locomotion" in post_selected:
                errors.append(name + ":candidate_stale_selected")
            if not isinstance(deferred, list) or not any(isinstance(d, dict) and d.get("proposal_id") == "deopt-g1" and d.get("reason") == "STALE_RESOURCE_GENERATION" for d in deferred):
                errors.append(name + ":candidate_stale_reason")
            if row.get("stale_submit_count") != 0 or row.get("stale_exec") is not None:
                errors.append(name + ":candidate_stale_execution")
            fresh = row.get("fresh_arbitration")
            if not isinstance(fresh, dict) or fresh.get("selected", {}).get("locomotion", {}).get("proposal_id") != "deopt-g2":
                errors.append(name + ":candidate_fresh_selection")
            if not release_ok(row.get("fresh_exec")):
                errors.append(name + ":candidate_fresh_execution")
        else:
            errors.append(name + ":unknown_arm")
    return {"decision": "PASS_AUDITOR_IDENTITY_BINDING_SCOPED" if not errors else "FAIL_AUDITOR_IDENTITY_BINDING_SCOPED",
            "errors": errors, "case_count": len(rows), "scope": "synthetic-audit-contract-only"}


def main():
    if OUT_PATH.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_EXISTS")
    fixture_bytes = FIXTURE_PATH.read_bytes()
    fixture = json.loads(fixture_bytes)
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    result = audit(raw, fixture, fixture_bytes)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
