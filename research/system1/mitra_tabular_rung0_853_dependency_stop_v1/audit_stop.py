#!/usr/bin/env python3
"""Raw-only auditor for the frozen Mitra dependency STOP record."""
import hashlib
import json
import pathlib
import re
import sys


def audit(root):
    root = pathlib.Path(root)
    errors = []
    lock = (root / "requirements.lock").read_bytes()
    manifest_raw = (root / "wheelhouse-manifest.json").read_bytes()
    prov = json.loads((root / "ACQUISITION_PROVENANCE.json").read_text(encoding="utf-8"))
    log = (root / "offline-install-import-preflight.log").read_bytes()
    log_text = log.decode("utf-8", "replace")
    manifest = json.loads(manifest_raw)
    artifacts = prov.get("artifacts", [])
    if hashlib.sha256(lock).hexdigest() != "d871eb53e8ed38d5ee5d2c8fbae8ed0b2a3f265523bbf24b0573f42b17864ec9":
        errors.append("lock_sha256")
    if hashlib.sha256(manifest_raw).hexdigest() != "158297ee664e598b0648970eb9b630dce7055f0fa75f2ce85a0bb8d700e2e48b":
        errors.append("manifest_sha256")
    if hashlib.sha256(log).hexdigest() != "85fbaFaf2397165491b9b6eAaF3445D40c7CB77EC687cB5D342A8F10CE7A8F2F".lower():
        errors.append("log_sha256")
    if len(manifest) != 59 or len(artifacts) != 59 or prov.get("count") != 59:
        errors.append("artifact_count")
    total = sum(x.get("bytes", -1) for x in manifest)
    if total != 195307446 or prov.get("bytes") != total:
        errors.append("artifact_bytes")
    if prov.get("manifest_sha256") != hashlib.sha256(manifest_raw).hexdigest():
        errors.append("provenance_manifest_identity")
    if prov.get("errors") != []:
        errors.append("acquisition_errors")
    expected = {x["file"]: (x["sha256"], x["bytes"]) for x in manifest}
    actual = {x.get("file"): (x.get("sha256"), x.get("bytes")) for x in artifacts}
    if actual != expected:
        errors.append("provenance_artifact_identity")
    urls = [x.get("file_url") for x in artifacts]
    if any(not u or not u.startswith("https://files.pythonhosted.org/") for u in urls):
        errors.append("distribution_urls")
    if not re.search(r"OFFLINE_INSTALL_EXIT=0\b", log_text):
        errors.append("offline_install_not_successful")
    if "ModuleNotFoundError: No module named 'omegaconf'" not in log_text:
        errors.append("expected_import_stop_missing")
    if "/autogluon/tabular/models/mitra/sklearn_interface.py" not in log_text or "config_pretrain.py" not in log_text:
        errors.append("target_import_not_proven")
    if re.search(r"(?im)^\s*(?:formal_predictions|prediction_count|optimizer_steps)\s*[=:]\s*[1-9]\d*", log_text):
        errors.append("formal_work_claimed")
    return errors


if __name__ == "__main__":
    problems = audit(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).parent)
    print(json.dumps({"disposition": "STOP_LOCAL_ARTIFACT_OR_RUNTIME" if not problems else "AUDIT_FAIL", "errors": problems}, sort_keys=True))
    raise SystemExit(bool(problems))

