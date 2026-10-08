"""Independent lifecycle and corruption-control audit for Issue #3644."""
import hashlib
import json
import sys
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def classify(raw):
    if raw.get("allocation_id") != "issue3657-launcher-reap-order-formal-01":
        return "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
    if raw.get("operations") != {"geometry": 0, "focus": 0, "input": 0,
                                  "model": 0, "network": 0}:
        return "FAIL_PROCESS_GROUP_CLEANUP"
    unit = raw.get("audit_unit_tests", {})
    if unit.get("returncode") != 0 or "Ran 6 tests" not in unit.get("stderr", ""):
        return "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
    if raw.get("decision") == "STOP_PRIVATE_CALC_NOT_READY":
        return "STOP_PRIVATE_CALC_NOT_READY"
    owner = raw.get("window_owner")
    launch = raw.get("launch", {})
    sentinel = raw.get("sentinel", {})
    cleanup = raw.get("cleanup", {})
    if not owner or not owner.get("proc"):
        return "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
    owner_proc = owner["proc"]
    pgid = launch.get("pgid_expected")
    before = raw.get("group_members_before", [])
    group_bound = (owner_proc.get("pgid") == pgid and owner_proc.get("sid") == pgid
                   and any(m.get("pid") == owner_proc.get("pid")
                           and m.get("start_ticks") == owner_proc.get("start_ticks")
                           for m in before))
    if not group_bound:
        return "FAIL_PROCESS_GROUP_CLEANUP"
    if raw.get("termination", {}).get("attempts") != 1:
        return "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
    if launch.get("reap_during_protocol") is not True:
        return "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
    samples = raw.get("samples_after", [])
    if not samples:
        return "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
    last = samples[-1]
    if last.get("owner_same_identity_alive") or last.get("xid_visible"):
        return "FAIL_PROCESS_GROUP_CLEANUP"
    if last.get("group_members"):
        return "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
    if sentinel.get("alive_after_group_signal") is not True:
        return "FAIL_PROCESS_GROUP_CLEANUP"
    if (not launch.get("reaped") or not sentinel.get("reaped")
            or not cleanup.get("xvfb_reaped", cleanup.get("xvfb_returncode") is not None)
            or not cleanup.get("x_socket_absent")):
        return "HOLD_PROCESS_OWNERSHIP_UNRESOLVED"
    return "PASS_PRIVATE_PROCESS_GROUP_CLEANUP_SCOPED"


def passing_fixture():
    return {
        "allocation_id": "issue3657-launcher-reap-order-formal-01",
        "decision": "PASS_PRIVATE_PROCESS_GROUP_CLEANUP_SCOPED",
        "operations": {"geometry": 0, "focus": 0, "input": 0,
                       "model": 0, "network": 0},
        "audit_unit_tests": {"returncode": 0, "stderr": "Ran 6 tests"},
        "launch": {"pgid_expected": 100, "reaped": True,
                   "reap_during_protocol": True},
        "window_owner": {"xid": 500, "proc": {"pid": 101,
                           "start_ticks": "777", "pgid": 100, "sid": 100}},
        "group_members_before": [{"pid": 100, "start_ticks": "700"},
                                 {"pid": 101, "start_ticks": "777"}],
        "termination": {"attempts": 1},
        "samples_after": [{"group_members": [],
                           "owner_same_identity_alive": False,
                           "xid_visible": False}],
        "sentinel": {"alive_after_group_signal": True, "reaped": True},
        "cleanup": {"xvfb_returncode": -15, "xvfb_reaped": True,
                    "x_socket_absent": True},
    }


def main(raw_path, out_path):
    raw = json.loads(Path(raw_path).read_text())
    claimed = raw.get("raw_sha256")
    unsigned = dict(raw)
    unsigned.pop("raw_sha256", None)
    raw_integrity = digest(unsigned) == claimed
    errors = [] if raw_integrity else ["raw_digest_mismatch"]
    source_dir = Path(__file__).resolve().parent
    repo_root = source_dir if source_dir.name == "src" else source_dir.parents[3]
    freeze = json.loads((source_dir / "FREEZE.json").read_text())
    manifest_path = source_dir / "SOURCE_MANIFEST.json"
    manifest_hash = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    if manifest_hash != freeze.get("source_manifest_sha256"):
        errors.append("source_manifest_digest_mismatch")
    manifest = json.loads(manifest_path.read_text())
    for rel, expected in manifest.get("files", {}).items():
        try:
            rel_path = Path(rel)
            source_path = (repo_root / rel_path.relative_to("research/integration/issue_3657_launcher_reap_order_v1")
                           if source_dir.name == "src" else repo_root / rel_path)
            actual = hashlib.sha256(source_path.read_bytes()).hexdigest()
        except OSError:
            actual = None
        if actual != expected:
            errors.append("source_file_digest_mismatch:" + rel)
    if raw.get("source_base_commit") != freeze.get("source_base_commit"):
        errors.append("source_base_commit_mismatch")
    if raw.get("image_id_asserted") != freeze.get("image_id"):
        errors.append("container_image_id_mismatch")
    decision = classify(raw)
    if decision != raw.get("decision"):
        errors.append("runner_auditor_decision_disagreement")
    # Adversarial mutations must never leave the original PASS classification.
    challenges = {}
    baseline = json.loads(json.dumps(raw))
    baseline.update(passing_fixture())
    mutations = {
        "owner-group-forged": lambda x: x["window_owner"]["proc"].update(pgid=-1),
        "owner-retained": lambda x: x["samples_after"][-1].update(owner_same_identity_alive=True),
        "xid-retained": lambda x: x["samples_after"][-1].update(xid_visible=True),
        "sentinel-killed": lambda x: x["sentinel"].update(alive_after_group_signal=False),
        "group-retained": lambda x: x["samples_after"][-1].update(group_members=[{"pid": 101}]),
    }
    for name, mutate in mutations.items():
        altered = json.loads(json.dumps(baseline))
        mutate(altered)
        challenges[name] = classify(altered) != "PASS_PRIVATE_PROCESS_GROUP_CLEANUP_SCOPED"
    tampered = json.loads(json.dumps(baseline))
    tampered["window_owner"]["xid"] = -1
    tampered_unsigned = dict(tampered)
    tampered_unsigned.pop("raw_sha256", None)
    challenges["raw-digest-mutation"] = digest(tampered_unsigned) != baseline["raw_sha256"]
    if not all(challenges.values()):
        errors.append("corruption_challenge_missed")
    result = {"decision": decision if raw_integrity and not errors else
              "HOLD_PROCESS_OWNERSHIP_UNRESOLVED",
              "runner_decision": raw.get("decision"),
              "raw_sha256": claimed, "raw_integrity_verified": raw_integrity,
              "errors": errors, "corruption_challenges_detected": challenges}
    Path(out_path).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
