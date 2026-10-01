import argparse
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ledger_errors(input_root, freeze_path, result_path):
    errors = []
    try:
        root = Path(input_root).resolve(strict=True)
        freeze = json.loads(Path(freeze_path).read_bytes())
        result = json.loads(Path(result_path).read_bytes())
        manifest_path = (root / "MANIFEST.json.b64").resolve(strict=True)
        if not manifest_path.is_relative_to(root):
            return ["V3_UNSAFE_MANIFEST_PATH"]
        manifest_bytes = base64.b64decode(
            manifest_path.read_bytes().strip(),
            validate=True,
        )
        manifest = json.loads(manifest_bytes)
        if sha(manifest_bytes) != freeze.get("manifest_sha256"):
            errors.append("V2_MANIFEST_SHA256_MISMATCH")
        declared = freeze.get("input_sha256")
        table = manifest.get("inputs")
        if not isinstance(declared, dict) or not isinstance(table, dict):
            return ["V2_INPUT_LEDGER_UNAVAILABLE"]
        recomputed = {}
        for key, entry in table.items():
            rel = Path(entry["path"])
            if rel.is_absolute() or ".." in rel.parts:
                errors.append("V2_UNSAFE_INPUT_PATH:" + key)
                continue
            path = root / (str(rel) + ".b64" if key == "delivered_prefix" else str(rel))
            try:
                resolved = path.resolve(strict=True)
            except (OSError, RuntimeError):
                errors.append("V3_INPUT_RESOLUTION_FAILED:" + key)
                continue
            if not resolved.is_relative_to(root):
                errors.append("V3_UNSAFE_INPUT_PATH:" + key)
                continue
            data = resolved.read_bytes()
            if key == "delivered_prefix":
                data = base64.b64decode(data.strip(), validate=True)
            digest = sha(data)
            recomputed[key] = {"path": entry.get("path"), "sha256": digest}
            if digest != entry.get("sha256") or declared.get(key) != digest:
                errors.append("V2_FROZEN_INPUT_HASH_MISMATCH:" + key)
        if set(recomputed) != set(table) or set(declared) != set(table):
            errors.append("V2_INPUT_LEDGER_KEYSET_MISMATCH")
        # Bind the copied result's complete path+digest ledger, not just the
        # separately frozen input table.
        if result.get("input_sha256") != recomputed:
            errors.append("V2_REPORTED_INPUT_LEDGER_MISMATCH")
    except Exception as exc:
        errors.append("V3_LEDGER_CHECK_EXCEPTION:" + type(exc).__name__)
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--audit-v1", default="/study/source/audit.py")
    args = parser.parse_args()
    cp = subprocess.run(
        [sys.executable, "-B", args.audit_v1, "--input-root", args.input_root,
         "--freeze", args.freeze, "--result", args.result],
        capture_output=True, text=True, timeout=20,
    )
    try:
        v1 = json.loads(cp.stdout)
    except Exception:
        v1 = {"decision": "FAIL", "errors": ["V1_OUTPUT_INVALID"]}
    errors = list(v1.get("errors", []))
    if cp.returncode != 0 and not errors:
        errors.append("V1_EXIT_NONZERO_WITHOUT_ERRORS")
    errors.extend(ledger_errors(args.input_root, args.freeze, args.result))
    out = {
        "schema": "issue4649-independent-audit-v3-ledger-confined",
        "decision": "PASS_INDEPENDENT" if not errors and v1.get("decision") == "PASS_INDEPENDENT" else "FAIL",
        "v1_decision": v1.get("decision"),
        "v1_errors": v1.get("errors", []),
        "errors": errors,
        "v1_stderr": cp.stderr,
    }
    print(json.dumps(out, sort_keys=True))
    return 0 if out["decision"] == "PASS_INDEPENDENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
