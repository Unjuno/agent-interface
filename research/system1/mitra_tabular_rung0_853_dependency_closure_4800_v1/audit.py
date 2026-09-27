#!/usr/bin/env python3
"""Independent raw-only auditor for the #4800 dependency closure evidence."""
import base64
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent

def main():
    meta = json.loads((ROOT / "EVIDENCE.json").read_text(encoding="utf-8-sig"))
    errors = []
    raw = {}
    for artifact in meta["artifacts"]:
        try:
            encoded = (ROOT / artifact["envelope"]).read_text(encoding="ascii").strip()
            data = base64.b64decode(encoded, validate=True)
        except Exception as exc:
            errors.append(f"envelope:{artifact['envelope']}:{type(exc).__name__}")
            continue
        raw[(artifact["revision"], artifact["role"])] = data
        if len(data) != artifact["bytes"]:
            errors.append(f"byte_length:{artifact['envelope']}")
        if hashlib.sha256(data).hexdigest() != artifact["sha256"]:
            errors.append(f"sha256:{artifact['envelope']}")
    for outcome in meta["outcomes"]:
        rev = outcome["revision"]
        data = raw.get((rev, "log"))
        if data is None:
            errors.append(f"missing_log:{rev}")
            continue
        text = data.decode("utf-8", "replace")
        for marker in outcome["markers"]:
            if marker not in text:
                errors.append(f"marker:{rev}:{marker}")
    expected = {"rev2": (62, 195565575), "rev3": (63, 195629934), "rev4": (64, 195793700)}
    manifests = {}
    for rev, (count, total_bytes) in expected.items():
        data = raw.get((rev, "manifest"))
        if data is None:
            errors.append(f"missing_manifest:{rev}")
            continue
        try:
            rows = json.loads(data.decode("utf-8-sig"))
            manifests[rev] = {row.get("file", "").lower().replace("_", "-"): row for row in rows}
            if len(rows) != count:
                errors.append(f"manifest_count:{rev}")
            if sum(row.get("bytes", -1) for row in rows) != total_bytes:
                errors.append(f"manifest_total_bytes:{rev}")
            if any(not re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")) for row in rows):
                errors.append(f"manifest_digest_shape:{rev}")
        except Exception as exc:
            errors.append(f"manifest_json:{rev}:{type(exc).__name__}")
    try:
        sources = json.loads((ROOT / "SOURCES.json").read_text(encoding="utf-8-sig"))
        lock = raw.get(("rev4", "lock"), b"").decode("ascii")
        for src in sources:
            if not src.get("url", "").startswith("https://files.pythonhosted.org/"):
                errors.append(f"source_url:{src.get('name')}")
            if not src.get("sha256", "") in lock:
                errors.append(f"source_not_locked:{src.get('name')}")
            row = manifests.get("rev4", {}).get(src.get("filename", "").lower().replace("_", "-"))
            if row is None or row.get("sha256") != src.get("sha256") or row.get("bytes") != src.get("bytes"):
                errors.append(f"source_manifest_mismatch:{src.get('name')}")
            if not (src.get("pypi_license_metadata") or src.get("embedded_license")):
                errors.append(f"license_evidence_missing:{src.get('name')}")
    except Exception as exc:
        errors.append(f"sources_json:{type(exc).__name__}")
    if meta.get("cuda_device_requested") is not False or meta.get("model_weights_loaded") is not False or meta.get("formal_predictions") != 0:
        errors.append("scope_violation")
    print(json.dumps({"audit": "PASS_RAW_DEPENDENCY_IMPORT_EVIDENCE" if not errors else "FAIL_EVIDENCE_INTEGRITY", "artifacts": len(meta["artifacts"]), "errors": errors}, sort_keys=True))
    return bool(errors)

if __name__ == "__main__":
    raise SystemExit(main())
