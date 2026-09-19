import json
import subprocess
import sys
out = subprocess.check_output([sys.executable, "experiment.py"], text=True)
result = json.loads(out)
assert result["decision"] == "PASS_TEMPORAL_OBSERVATION_FIXTURE_SCOPED"
assert all(result["cases"].values())
assert all(result["controls"].values())
assert result["construction_invocations"] == 0
assert result["gui_x11_model_network_input"] == 0
print("INDEPENDENT_AUDIT_PASS", result["sha256"])
