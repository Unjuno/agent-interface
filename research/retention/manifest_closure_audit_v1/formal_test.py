from __future__ import annotations

import hashlib
import json
from pathlib import Path

from auditor import audit_inventory, audit_local

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / "CASE_SNAPSHOT.json"
RESULT = ROOT / "RESULT.json"


def evidence_text(files):
    return "\n".join(f"{hashlib.sha256(data).hexdigest()}  {name}" for name, data in files.items()) + "\n"


def base_synthetic():
    files = {
        "FORMAL_BATCHES.tar.gz.b64.part00": b"formal-0",
        "FORMAL_BATCHES.tar.gz.b64.part01": b"formal-1",
        "SOURCE_BUNDLE.tar.gz.b64.part00": b"source-0",
        "REPORT.md": b"report",
    }
    manifest = {
        "formal_batches_parts": [
            "FORMAL_BATCHES.tar.gz.b64.part00",
            "FORMAL_BATCHES.tar.gz.b64.part01",
        ],
        "source_bundle_parts": ["SOURCE_BUNDLE.tar.gz.b64.part00"],
    }
    return manifest, files, evidence_text(files)


def expect(name, got, disposition, extra=None):
    row = {"case": name, "expected": disposition, "got": got["disposition"], "pass": got["disposition"] == disposition}
    if extra is not None:
        row["extra_pass"] = bool(extra(got))
        row["pass"] = row["pass"] and row["extra_pass"]
    return row


def main():
    snap = json.loads(SNAPSHOT.read_text())
    cases = []

    real = audit_inventory(snap["retention_manifest"], snap["evidence_sha256"], snap["inventory"])
    missing_expected = [
        "FORMAL_BATCHES.tar.gz.b64.part03",
        "FORMAL_BATCHES.tar.gz.b64.part04",
        "FORMAL_BATCHES.tar.gz.b64.part05",
        "FORMAL_BATCHES.tar.gz.b64.part06",
    ]
    cases.append(expect("real_1459_inventory", real, "FAIL_MISSING", lambda r: r.get("missing") == missing_expected))

    manifest, files, evidence = base_synthetic()
    mtext = json.dumps(manifest, sort_keys=True)
    cases.append(expect("complete_inventory", audit_inventory(mtext, evidence, files.keys()), "PASS"))
    cases.append(expect("complete_local", audit_local(mtext, evidence, files), "PASS"))

    missing_files = dict(files)
    missing_files.pop("FORMAL_BATCHES.tar.gz.b64.part01")
    cases.append(expect("one_missing_part", audit_inventory(mtext, evidence, missing_files.keys()), "FAIL_MISSING"))

    corrupt_files = dict(files)
    corrupt_files["REPORT.md"] = b"report-corrupt"
    cases.append(expect("one_corrupt_byte", audit_local(mtext, evidence, corrupt_files), "FAIL_HASH"))

    evidence_lines = evidence.splitlines()
    disagree = "\n".join(line for line in evidence_lines if not line.endswith("FORMAL_BATCHES.tar.gz.b64.part01")) + "\n"
    cases.append(expect("manifest_evidence_disagreement", audit_inventory(mtext, disagree, files.keys()), "FAIL_MANIFEST_EVIDENCE"))

    unsafe_evidence = evidence + ("0" * 64) + "  ../escape.bin\n"
    cases.append(expect("unsafe_path", audit_inventory(mtext, unsafe_evidence, list(files) + ["../escape.bin"]), "FAIL_UNSAFE_PATH"))

    duplicate_evidence = evidence + evidence.splitlines()[0] + "\n"
    cases.append(expect("duplicate_evidence", audit_inventory(mtext, duplicate_evidence, files.keys()), "FAIL_DUPLICATE"))

    malformed = evidence.replace(evidence.split()[0], "not-a-sha", 1)
    cases.append(expect("malformed_sha", audit_inventory(mtext, malformed, files.keys()), "FAIL_SCHEMA"))

    passed = all(row["pass"] for row in cases)
    out = {
        "task": "MANIFEST-CLOSURE-AUDITOR-20260918-001",
        "formal_invocations": 1,
        "reruns": 0,
        "cases": cases,
        "real_1459_observation": real,
        "decision": "PASS_MANIFEST_CLOSURE_AUDITOR_SCOPED" if passed else "FAIL_AUDITOR_UNSAFE",
        "pass": passed,
    }
    RESULT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, sort_keys=True))
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
