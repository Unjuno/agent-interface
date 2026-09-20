from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import audit as independent_oracle


ROOT = Path("/evidence")
INPUT = Path("/input")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def corruption_controls(raw: dict) -> list[dict]:
    challenges = []
    base, _ = independent_oracle.reconstruct(raw)
    mutations = [
        ("row-dropped", lambda x: x["rows"].pop()),
        ("row-duplicated", lambda x: x["rows"].append(copy.deepcopy(x["rows"][0]))),
        ("xid-mutated", lambda x: x["pairs"][0]["g2"]["identity"]["top_level_client_id"].update(value=4)),
        ("same-token", lambda x: x["pairs"][0]["g2"].update(server_instance_id=x["pairs"][0]["g1"]["server_instance_id"])),
        ("authority-escalated", lambda x: x["rows"][0]["receipt"].update(authority="task-input")),
        ("socket-lifecycle-removed", lambda x: x["pairs"][0]["g1_cleanup"].update(socket_disappeared=False)),
        ("runner-decision-forged", lambda x: x.update(decision="UNSUPPORTED_FORGED_DECISION")),
        ("issued-receipt-removed", lambda x: x["issued_receipts"].pop()),
    ]
    for name, mutate in mutations:
        changed = copy.deepcopy(raw)
        mutate(changed)
        disposition, _ = independent_oracle.reconstruct(changed)
        challenges.append({"name": name, "detected": disposition != base,
                           "mutated_disposition": disposition})

    # Start from a scientific lifetime escape, then claim PASS in the runner field.
    # The independent row oracle must still reject it; candidate labels never grant acceptance.
    escape = copy.deepcopy(raw)
    for row in escape["rows"]:
        if row["case"] == "cross_generation_stale" and row["policy"] == "LIFETIME_BOUND":
            row["bound"] = "ACCEPT"
            row["bound_result"] = {"classification": "ACCEPT", "reason": row["typed"]["reason"]}
    escape["decision"] = "PASS_XSERVER_LIFETIME_BINDING_REQUIRED_SCOPED"
    disposition, reasons = independent_oracle.reconstruct(escape)
    challenges.append({"name": "forged-pass-over-lifetime-escape",
                       "detected": disposition != "PASS_XSERVER_LIFETIME_BINDING_REQUIRED_SCOPED",
                       "mutated_disposition": disposition, "reasons": reasons})
    return challenges


def main() -> None:
    raw_bytes = (INPUT / "raw.json").read_bytes()
    freeze_bytes = Path("/freeze.json").read_bytes()
    manifest_bytes = Path("/source_manifest.json").read_bytes()
    audit_freeze_bytes = Path("/audit_freeze.json").read_bytes()
    audit_manifest_bytes = Path("/audit_manifest.json").read_bytes()
    raw, freeze, manifest = json.loads(raw_bytes), json.loads(freeze_bytes), json.loads(manifest_bytes)
    audit_freeze, audit_manifest = json.loads(audit_freeze_bytes), json.loads(audit_manifest_bytes)
    errors = []
    if sha(freeze_bytes) != raw.get("freeze_sha256"):
        errors.append("raw/freeze SHA-256 mismatch")
    if sha(manifest_bytes) != raw.get("source_manifest_sha256"):
        errors.append("raw/source manifest SHA-256 mismatch")
    if freeze.get("source_manifest_sha256") != sha(manifest_bytes):
        errors.append("freeze/source manifest SHA-256 mismatch")
    if freeze.get("source_commit") != raw.get("source_commit"):
        errors.append("source commit differs from frozen anchor")
    if freeze.get("container", {}).get("image_id") != raw.get("image_id"):
        errors.append("image identity differs from freeze")
    if sha(audit_manifest_bytes) != audit_freeze.get("audit_manifest_sha256"):
        errors.append("audit manifest hash differs from audit freeze")
    if sha(raw_bytes) != audit_freeze.get("input_raw_sha256"):
        errors.append("raw hash differs from audit freeze")
    if audit_manifest.get("input", {}).get("raw_sha256") != sha(raw_bytes):
        errors.append("audit manifest raw hash mismatch")
    for rel, expected in audit_manifest.get("source_files", {}).items():
        p = Path("/candidate") / rel
        if not p.is_file() or sha(p.read_bytes()) != expected:
            errors.append(f"audit source hash mismatch: {rel}")
    for rel, expected in manifest.get("files", {}).items():
        p = Path("/candidate") / rel
        if not p.is_file() or sha(p.read_bytes()) != expected:
            errors.append(f"source file hash mismatch: {rel}")
    result_hash = raw.get("result_sha256")
    result_payload = dict(raw)
    result_payload.pop("result_sha256", None)
    canonical = json.dumps(result_payload, sort_keys=True, separators=(",", ":")).encode()
    if sha(canonical) != result_hash:
        errors.append("result self-hash mismatch")
    disposition, reconstruction_errors = independent_oracle.reconstruct(raw)
    errors.extend(reconstruction_errors)
    controls = corruption_controls(raw)
    if len(controls) < 9 or not all(c["detected"] for c in controls):
        errors.append("one or more independent corruption challenges were not detected")
    final = disposition if not errors else "STOP_OR_HOLD_AUDIT_V2"
    audit = {
        "audit": "PASS_INDEPENDENT_LIFETIME_AUDIT" if final == "PASS_XSERVER_LIFETIME_BINDING_REQUIRED_SCOPED" else "STOP_OR_HOLD_AUDIT_V2",
        "candidate_decision": raw.get("decision"),
        "independent_decision": final,
        "raw_sha256": sha(raw_bytes),
        "freeze_sha256": sha(freeze_bytes),
        "source_manifest_sha256": sha(manifest_bytes),
        "result_sha256_verified": not any("result self-hash" in e for e in errors),
        "source_files_verified": not any("source file hash" in e for e in errors),
        "row_count": len(raw.get("rows", [])),
        "pair_count": len(raw.get("pairs", [])),
        "negative_control_count": len(raw.get("negative_controls", [])),
        "corruption_controls": controls,
        "errors": errors,
    }
    (ROOT / "audit_v2.json").write_text(json.dumps(audit, sort_keys=True, indent=2) + "\n")
    print(json.dumps(audit, sort_keys=True))
    if final not in {"PASS_XSERVER_LIFETIME_BINDING_REQUIRED_SCOPED", "FAIL_LIFETIME_ESCAPE",
                     "FAIL_LIFETIME_OVERINVALIDATION", "HOLD_NO_XID_REUSE_DISCRIMINATOR"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
