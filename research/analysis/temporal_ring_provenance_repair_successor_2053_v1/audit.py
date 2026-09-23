import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
runner = ROOT / "formal.py"
with tempfile.TemporaryDirectory() as td:
    completed = subprocess.run([sys.executable, str(runner)], cwd=td, check=True, text=True, capture_output=True)
    result = json.loads(completed.stdout)
assert Path(result["result_path"]).resolve() == (ROOT / "result.json").resolve()
assert result["decision"] == "PASS_TEMPORAL_RING_PROVENANCE_REPAIR_SCOPED"
assert result["cases"] == 10 and result["unknown_cases"] == 8
assert result["mismatches"] == 0
assert result["model_gui_network_runtime_task_input"] == 0
print("INDEPENDENT_AUDIT_PASS", result["sha256"])
