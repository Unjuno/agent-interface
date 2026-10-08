import subprocess
import sys
import json
import hashlib
from pathlib import Path

here = Path(__file__).parent
out = Path(sys.argv[1])
prior = Path(sys.argv[2])
freeze = json.loads((here / "FREEZE.json").read_bytes())
source_hashes = {}
source_errors = []
for rel, expected in freeze["sha256"].items():
    actual = hashlib.sha256((here / rel).read_bytes()).hexdigest()
    source_hashes[rel] = actual
    if actual != expected:
        source_errors.append(rel)
identity = {"allocation": freeze["allocation"], "source_sha256": source_hashes, "source_errors": source_errors}
(out / "execution.json").write_text(json.dumps(identity, sort_keys=True, indent=2) + "\n")
if source_errors:
    raise SystemExit("FROZEN_SOURCE_MISMATCH:" + ",".join(source_errors))
tests = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_effect_oracle"], cwd=here, capture_output=True, text=True)
(out / "tests.stdout").write_text(tests.stdout)
(out / "tests.stderr").write_text(tests.stderr)
if tests.returncode:
    raise SystemExit(tests.returncode)
audit = subprocess.run([sys.executable, "-B", str(here / "run_audit.py"), str(prior), str(out / "formal01")], cwd=here, capture_output=True, text=True)
(out / "audit.stdout").write_text(audit.stdout)
(out / "audit.stderr").write_text(audit.stderr)
if audit.returncode:
    raise SystemExit(audit.returncode)

