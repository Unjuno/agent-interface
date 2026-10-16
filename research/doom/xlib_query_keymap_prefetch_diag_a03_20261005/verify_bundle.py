"""Verify frozen source hashes inside the extracted diagnostic bundle."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
freeze = json.loads((ROOT / "FREEZE.json").read_text())
checks = {"freeze_base": freeze.get("main_sha") == "c520359ee10b8071d13f2e93e82bd840a81eabda"}
for name, expected in freeze["source_sha256"].items():
    checks["sha256:" + name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected
manifest = {}
for line in (ROOT / "SHA256SUMS").read_text().splitlines():
    digest, name = line.split("  ", 1)
    manifest[name] = digest
for name in list(freeze["source_sha256"]) + ["FREEZE.json"]:
    checks["manifest:" + name] = manifest.get(name) == hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
result = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}
print(json.dumps(result, sort_keys=True))
raise SystemExit(0 if result["status"] == "PASS" else 1)
