from __future__ import annotations

import hashlib
import json
import re
from pathlib import PurePosixPath
from typing import Mapping, Iterable

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FORMAL_PREFIX = "FORMAL_BATCHES.tar.gz.b64.part"
_SOURCE_PREFIX = "SOURCE_BUNDLE.tar.gz.b64.part"


def _safe_path(name: str) -> bool:
    if not isinstance(name, str) or not name or "\\" in name:
        return False
    p = PurePosixPath(name)
    if p.is_absolute():
        return False
    return all(part not in ("", ".", "..") for part in p.parts)


def _fail(code: str, **details):
    return {"ok": False, "disposition": code, **details}


def _parse_manifest(text: str):
    try:
        obj = json.loads(text)
    except Exception as exc:
        return None, _fail("FAIL_SCHEMA", field="manifest_json", error=type(exc).__name__)
    if not isinstance(obj, dict):
        return None, _fail("FAIL_SCHEMA", field="manifest_type")
    formal = obj.get("formal_batches_parts")
    source = obj.get("source_bundle_parts")
    if not isinstance(formal, list) or not isinstance(source, list):
        return None, _fail("FAIL_SCHEMA", field="manifest_parts")
    parts = formal + source
    if not all(isinstance(x, str) for x in parts):
        return None, _fail("FAIL_SCHEMA", field="manifest_part_type")
    if len(parts) != len(set(parts)):
        return None, _fail("FAIL_DUPLICATE", field="manifest_parts")
    for name in parts:
        if not _safe_path(name):
            return None, _fail("FAIL_UNSAFE_PATH", path=name, source="manifest")
    return {"obj": obj, "formal": formal, "source": source, "parts": parts}, None


def _parse_evidence(text: str):
    entries: dict[str, str] = {}
    for line_no, raw in enumerate(text.splitlines(), 1):
        if not raw.strip():
            continue
        pieces = raw.strip().split(None, 1)
        if len(pieces) != 2:
            return None, _fail("FAIL_SCHEMA", field="evidence_line", line=line_no)
        digest, name = pieces[0].lower(), pieces[1].strip()
        if not _SHA256.fullmatch(digest):
            return None, _fail("FAIL_SCHEMA", field="sha256", line=line_no, value=digest)
        if not _safe_path(name):
            return None, _fail("FAIL_UNSAFE_PATH", path=name, source="evidence", line=line_no)
        if name in entries:
            return None, _fail("FAIL_DUPLICATE", field="evidence_name", path=name, line=line_no)
        entries[name] = digest
    if not entries:
        return None, _fail("FAIL_SCHEMA", field="evidence_empty")
    return entries, None


def audit_inventory(manifest_text: str, evidence_text: str, inventory: Iterable[str]):
    manifest, error = _parse_manifest(manifest_text)
    if error:
        return error
    evidence, error = _parse_evidence(evidence_text)
    if error:
        return error

    inventory_list = list(inventory)
    if not all(isinstance(x, str) and _safe_path(x) for x in inventory_list):
        bad = next((x for x in inventory_list if not isinstance(x, str) or not _safe_path(x)), None)
        return _fail("FAIL_UNSAFE_PATH", path=bad, source="inventory")
    if len(inventory_list) != len(set(inventory_list)):
        return _fail("FAIL_DUPLICATE", field="inventory")

    declared = set(manifest["parts"])
    evidence_chunks = {
        name for name in evidence
        if name.startswith(_FORMAL_PREFIX) or name.startswith(_SOURCE_PREFIX)
    }
    if declared != evidence_chunks:
        return _fail(
            "FAIL_MANIFEST_EVIDENCE",
            manifest_only=sorted(declared - evidence_chunks),
            evidence_only=sorted(evidence_chunks - declared),
        )

    required = set(evidence) | declared
    present = set(inventory_list)
    missing = sorted(required - present)
    if missing:
        return _fail("FAIL_MISSING", missing=missing, required_count=len(required), present_count=len(present))

    return {
        "ok": True,
        "disposition": "PASS",
        "required_count": len(required),
        "manifest_part_count": len(declared),
        "evidence_count": len(evidence),
    }


def audit_local(manifest_text: str, evidence_text: str, files: Mapping[str, bytes]):
    inventory_result = audit_inventory(manifest_text, evidence_text, files.keys())
    if not inventory_result["ok"]:
        return inventory_result
    evidence, error = _parse_evidence(evidence_text)
    if error:
        return error
    mismatches = []
    for name, expected in evidence.items():
        data = files[name]
        if not isinstance(data, (bytes, bytearray)):
            return _fail("FAIL_SCHEMA", field="file_bytes", path=name)
        actual = hashlib.sha256(bytes(data)).hexdigest()
        if actual != expected:
            mismatches.append({"path": name, "expected": expected, "actual": actual})
    if mismatches:
        return _fail("FAIL_HASH", mismatches=mismatches)
    return {
        "ok": True,
        "disposition": "PASS",
        "verified_count": len(evidence),
    }
