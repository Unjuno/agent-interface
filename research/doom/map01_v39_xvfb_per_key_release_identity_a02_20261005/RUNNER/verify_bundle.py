import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
freeze = json.loads((ROOT / "FREEZE.json").read_text())
checks = {}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
checks["source_manifest"] = sha(ROOT / "SOURCE_BLOBS.json") == freeze["source_manifest_sha256"]
manifest = json.loads((ROOT / "SOURCE_BLOBS.json").read_text())
checks["source_manifest_base"] = manifest.get("base_commit") == freeze["base_commit"]
checks["source_manifest_blobs"] = manifest.get("blob_ids") == freeze["source_blob_ids"]
checks["source_manifest_digests"] = manifest.get("source_sha256") == freeze["source_sha256"]
checks["preregistration"] = sha(ROOT / "PREREGISTRATION.md") == freeze["preregistration_sha256"]
checks["readme"] = sha(ROOT / "README.md") == freeze["readme_sha256"]
checks["commands"] = sha(ROOT / "COMMANDS.txt") == freeze["commands_sha256"]
checks["candidate"] = sha(ROOT / "SOURCE/candidate.py") == freeze["candidate_sha256"]
checks["auditor"] = sha(ROOT / "SOURCE/audit.py") == freeze["auditor_sha256"]
checks["mutation_tests"] = sha(ROOT / "SOURCE/test_audit.py") == freeze["test_audit_sha256"]
checks["bundle_verifier"] = sha(ROOT / "RUNNER/verify_bundle.py") == freeze["verifier_sha256"]
checks["setup_runner"] = sha(ROOT / "RUNNER/setup_guest.sh") == freeze["setup_runner_sha256"]
checks["candidate_runner"] = sha(ROOT / "RUNNER/run_candidate.sh") == freeze["candidate_runner_sha256"]
manifest_rows = [line.split(None, 1) for line in (ROOT / "SHA256SUMS").read_text().splitlines() if line.strip()]
checks["sha256_manifest"] = bool(manifest_rows) and all(
    len(row) == 2 and sha(ROOT / row[1].lstrip("*")) == row[0] for row in manifest_rows
)
for name, digest in freeze["source_sha256"].items():
    checks["source:" + name] = sha(ROOT / "SOURCE/source" / name) == digest
ok = all(checks.values())
print(json.dumps({"status": "PASS" if ok else "STOP", "checks": checks}, sort_keys=True))
sys.exit(0 if ok else 1)
