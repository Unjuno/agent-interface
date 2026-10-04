"""Prove the saved A01 auditor rejects attempt-accounting corruption per route."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
for case_name in ("warm_changed", "outer_effect_unavailable"):
    for arm, filename in (("main", "RUN-MAIN.json"), ("candidate", "RUN-PR7330.json")):
        with tempfile.TemporaryDirectory(prefix="a01-audit-mutation-") as tmp:
            target = Path(tmp)
            shutil.copy2(root / "audit.py", target / "audit.py")
            data = json.loads((root / filename).read_text())
            result = data["cases"][case_name]["result"]
            result["accounting"]["attempted_calls"] = 1
            result["attempt_ledger"] = [{"mutation": "nonempty"}]
            (target / filename).write_text(json.dumps(data))
            # The unmodified second arm remains the control input.
            other = "RUN-PR7330.json" if arm == "main" else "RUN-MAIN.json"
            shutil.copy2(root / other, target / other)
            proc = subprocess.run(["python3", "-B", str(target / "audit.py")], capture_output=True, text=True)
            assert proc.returncode != 0, (arm, case_name, proc.stdout, proc.stderr)
print("PASS: main and candidate corruption in warm_changed and outer_effect_unavailable is rejected")
