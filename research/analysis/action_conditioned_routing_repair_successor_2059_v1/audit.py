import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as td:
    p=subprocess.run([sys.executable,str(ROOT/"experiment.py")],cwd=td,check=True,text=True,capture_output=True)
    result=json.loads(p.stdout)
assert Path(result.get("result_path", str(ROOT/"result.json"))).resolve() == (ROOT/"result.json").resolve() if "result_path" in result else True
assert result["decision"]=="PASS_ACTION_CONDITIONED_ROUTING_REPAIR_SCOPED"
assert result["cases"]==8 and result["mismatches"]==0
assert result["malformed_or_unknown"]==5
assert result["raw_retained_rows"]==8
assert result["authority_true"]==0
assert result["model_gui_network_runtime_task_input"]==0
print("INDEPENDENT_AUDIT_PASS",result["rows_sha256"])
