#!/usr/bin/env python3
"""Independent raw-record verifier; does not import candidate code."""
import copy
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
RAW = ROOT / "raw"
EXPECTED_DIFF = {
    "clean_single": {"C /workspace/single.txt"},
    "clean_multi_rename": {"C /workspace/alpha.txt", "D /workspace/beta.txt", "A /workspace/gamma.txt", "A /workspace/new.txt"},
    "clean_metadata_change": {"C /workspace/single.txt"},
    "partial_multifile_save": {"C /workspace/alpha.txt"},
    "network_effect_attempt": set(),
}
EXPECTED_FILES = {
    "clean_single": {"single.txt": "single-v2\n"},
    "clean_multi_rename": {"alpha.txt": "alpha-v2\n", "gamma.txt": "beta-v1\n", "new.txt": "new-v1\n"},
    "clean_metadata_change": {"single.txt": "base-single-v1\n"},
    "partial_multifile_save": {"alpha.txt": "alpha-partial\n", "beta.txt": "beta-v1\n"},
    "network_effect_attempt": {"single.txt": "base-single-v1\n"},
}
ACCEPT = {"clean_single", "clean_multi_rename", "clean_metadata_change"}


def digest(data):
    return hashlib.sha256(data.encode()).hexdigest()


def check(record):
    errors = []
    if record.get("schema") != "cow-7459-t0-candidate-v1":
        errors.append("schema")
    if record.get("image_build", {}).get("exit") != 0 or record.get("image_inspect", {}).get("exit") != 0:
        errors.append("image_provenance")
    freeze = record.get("freeze", {})
    frozen_file = RAW / "freeze.json"
    if not frozen_file.is_file() or hashlib.sha256(frozen_file.read_bytes()).hexdigest() != record.get("freeze_sha256"):
        errors.append("freeze_hash")
    if freeze.get("files_sha256") != record.get("source_sha256"):
        errors.append("freeze_source_identity")
    if "overlayfs" not in freeze.get("driver", "") or "linux/aarch64" not in freeze.get("driver", "").lower():
        errors.append("runtime_identity")
    cases = {x.get("id"): x for x in record.get("cases", [])}
    if len(cases) != 7 or len(cases) != len(record.get("cases", [])):
        errors.append("case_set")
    for cid, expected_diff in EXPECTED_DIFF.items():
        c = cases.get(cid)
        if not c:
            errors.append(f"missing:{cid}")
            continue
        raw_diff = {s.strip() for s in c.get("diff", {}).get("output", "").splitlines() if s.strip()}
        if raw_diff != expected_diff or set(c.get("diff_entries", [])) != expected_diff:
            errors.append(f"diff:{cid}")
        expected = {k: digest(v) for k, v in EXPECTED_FILES[cid].items()}
        if c.get("export_inventory") != expected or c.get("expected_inventory") != expected:
            errors.append(f"bytes:{cid}")
        if c.get("export_cp", {}).get("exit") != 0:
            errors.append(f"export:{cid}")
        if cid in ACCEPT:
            if c.get("decision") != "ACCEPT_DELTA" or any(op.get("exit") for op in c.get("ops", [])):
                errors.append(f"accept_gate:{cid}")
        else:
            if c.get("decision") == "ACCEPT_DELTA":
                errors.append(f"unsafe_accept:{cid}")
        try:
            decoder = json.JSONDecoder()
            cfg, n = decoder.raw_decode(c["inspect"]["output"])
            state, _ = decoder.raw_decode(c["inspect"]["output"][n:].lstrip())
            if cfg.get("NetworkMode") != "none" or cfg.get("IpcMode") != "private" or cfg.get("Binds"):
                errors.append(f"container_boundary:{cid}")
            if state.get("Running") is not False:
                errors.append(f"container_still_running:{cid}")
        except Exception:
            errors.append(f"inspect_parse:{cid}")
        if cid == "clean_metadata_change" and c.get("export_modes", {}).get("single.txt") != "600":
            errors.append("metadata")
        if cid == "partial_multifile_save" and not any(op.get("exit") == 23 for op in c.get("ops", [])):
            errors.append("partial_injection")
        if cid == "network_effect_attempt" and not any(op.get("exit") != 0 for op in c.get("ops", [])):
            errors.append("network_not_denied")
    for cid in ("dirty_open_buffer", "concurrent_base_revision_changed"):
        c = cases.get(cid, {})
        if c.get("container_created") is not False or c.get("decision") != "REFUSE_UNPROVABLE_STATE":
            errors.append(f"refusal:{cid}")
    controls = record.get("controls", {})
    direct = controls.get("direct_live", {})
    draft = controls.get("native_draft", {})
    base = {"single.txt": digest("base-single-v1\n")}
    changed = {"single.txt": digest("single-v2\n")}
    if direct.get("base_inventory") != changed:
        errors.append("direct_control")
    if draft.get("base_inventory") != base or draft.get("draft_inventory") != changed:
        errors.append("draft_control")
    # Verify that all declared source digests still match the frozen tree.
    for rel, expected in record.get("source_sha256", {}).items():
        p = ROOT / rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            errors.append(f"source_hash:{rel}")
    return errors


def main():
    p = RAW / "candidate.json"
    if not p.is_file():
        raise SystemExit("AUDIT_STOP_NO_CANDIDATE_RECORD")
    record = json.loads(p.read_text())
    errors = check(record)
    corruptions = []
    for name, mutate in [
        ("drop_delta_entry", lambda r: r["cases"][0]["diff_entries"].pop()),
        ("alter_export_hash", lambda r: r["cases"][0]["export_inventory"].update({"single.txt": "0" * 64})),
        ("false_accept_refusal", lambda r: next(x for x in r["cases"] if x["id"] == "dirty_open_buffer").__setitem__("decision", "ACCEPT_DELTA")),
        ("remove_network_denial", lambda r: next(x for x in r["cases"] if x["id"] == "network_effect_attempt")["ops"].__setitem__(0, {"exit": 0})),
    ]:
        clone = copy.deepcopy(record)
        mutate(clone)
        caught = bool(check(clone))
        corruptions.append({"id": name, "rejected": caught})
    if not all(x["rejected"] for x in corruptions):
        errors.append("auditor_corruption_control")
    audit = {"status": "PASS_SCOPED" if not errors else "FAIL_AUDIT", "case_count": len(record.get("cases", [])),
             "errors": errors, "corruption_controls": corruptions,
             "scope": "synthetic Docker-managed container overlay only; not macOS host APFS COW, GUI application consistency, or general process sandboxing"}
    (RAW / "audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(json.dumps(audit, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
