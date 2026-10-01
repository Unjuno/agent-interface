"""One-shot in-memory copied-raw hardening diagnostic."""
from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import types
import zipfile

from audit_hardened import AuditReject, audit_document, strict_load

EXPECTED_LEGACY_BLOB = "1a6cc0e46b32d4cd6989aed118d003cce4cfe399"
EXPECTED_ARCHIVE_BLOB = "c38dd2002f201d49b6fc261caff019550a4bf4bc"
EXPECTED_RAW_SHA256 = "5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d"


def git_blob(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode() + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def _reject(source: bytes, archive_text: bytes):
    if git_blob(source) != EXPECTED_LEGACY_BLOB:
        raise AuditReject("legacy source Git blob mismatch")
    if git_blob(archive_text) != EXPECTED_ARCHIVE_BLOB:
        raise AuditReject("archive Git blob mismatch")
    archive = base64.b64decode(archive_text.strip(), validate=True)
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        members = bundle.namelist()
        raw_name = next(name for name in members if name.lower().endswith("raw.json"))
        raw = bundle.read(raw_name)
    raw_sha = hashlib.sha256(raw).hexdigest()
    if raw_sha != EXPECTED_RAW_SHA256:
        raise AuditReject("extracted raw SHA-256 mismatch")
    return members, raw_name, raw, raw_sha


def run_bytes(legacy_source: bytes, archive_text: bytes) -> dict:
    members, raw_name, raw, raw_before = _reject(legacy_source, archive_text)
    legacy = types.ModuleType("frozen_legacy_audit")
    exec(compile(legacy_source, "frozen-main-audit.py", "exec"), legacy.__dict__)
    doc = strict_load(raw)
    hardened = audit_document(doc)
    original = legacy.audit(doc)
    if original.get("status") != "PASS_DRIFT_BOUNDARY_MAPPED" or original.get("errors") != []:
        raise AuditReject("unchanged predecessor baseline failed")
    if original.get("row_count") != 336 or original.get("corruption_controls_rejected") != 5:
        raise AuditReject("predecessor baseline cardinality/control mismatch")

    mutations = {}
    for label, mutate in (
        ("nan_weight", lambda data: data["distributions"][0]["rows"][0].__setitem__("weight", float("nan"))),
        ("development_alpha", lambda data: data.__setitem__("development_alpha", 0.5)),
        ("truth_state_count", lambda data: data.__setitem__("truth_state_count", 99)),
    ):
        changed = copy.deepcopy(doc)
        mutate(changed)
        try:
            encoded = json.dumps(changed, separators=(",", ":")).encode()
            decoded = strict_load(encoded)
            audit_document(decoded)
        except (AuditReject, ValueError, TypeError) as exc:
            mutations[label] = {"rejected": True, "reason": str(exc)}
        else:
            mutations[label] = {"rejected": False, "reason": ""}

    json_constants = {}
    for token in ("NaN", "Infinity", "-Infinity"):
        try:
            strict_load(("{\"value\":" + token + "}").encode())
        except AuditReject:
            json_constants[token] = "REJECTED"
        else:
            json_constants[token] = "ACCEPTED"

    weight_controls = {}
    for value in (True, "0", float("nan"), float("inf"), -float("inf"), 0.1):
        try:
            from audit_hardened import require_valid_weight
            require_valid_weight(value, 0.0)
        except AuditReject:
            weight_controls[repr(value)] = "REJECTED"
        else:
            weight_controls[repr(value)] = "ACCEPTED"

    raw_after = hashlib.sha256(raw).hexdigest()
    gap_closed = all(item["rejected"] for item in mutations.values())
    controls_closed = all(value == "REJECTED" for value in json_constants.values()) and all(
        value == "REJECTED" for value in weight_controls.values())
    return {
        "status": "PASS_AUDIT_HARDENING_SCOPED" if gap_closed and controls_closed else "FAIL_HARDENING_GAP_REMAINS",
        "runtime": "host-standard-library-python; Docker Engine unresponsive",
        "source_git_blob": git_blob(legacy_source),
        "archive_git_blob": git_blob(archive_text),
        "raw_member": raw_name,
        "zip_members": members,
        "raw_sha256_before": raw_before,
        "raw_sha256_after": raw_after,
        "rows": hardened["rows"],
        "distributions": hardened["distributions"],
        "crossover_alpha": hardened["first_cost_crossover_alpha"],
        "predecessor_audit": {
            "status": original["status"],
            "errors": original["errors"],
            "rows": original["row_count"],
            "corruption_controls_rejected": original["corruption_controls_rejected"],
            "corruption_control_count": original["corruption_control_count"],
        },
        "mutations": mutations,
        "json_constants": json_constants,
        "weight_controls": weight_controls,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-source", required=True)
    parser.add_argument("--archive-base64", required=True)
    args = parser.parse_args()
    with open(args.legacy_source, "rb") as stream:
        source = stream.read()
    with open(args.archive_base64, "rb") as stream:
        archive = stream.read()
    print(json.dumps(run_bytes(source, archive), sort_keys=True))


if __name__ == "__main__":
    main()
