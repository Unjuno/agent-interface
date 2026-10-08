import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as td:
 p=subprocess.run([sys.executable,str(ROOT/"experiment.py")],cwd=td,check=True,text=True,capture_output=True)
 r=json.loads(p.stdout)
assert r["decision"]=="PASS_ATTENTION_PROVENANCE_VALUE_REPAIR_SCOPED"
assert r["cases"]==11 and r["admitted"]==2 and r["unknown"]==9 and r["mismatches"]==0
assert r["authority_true"]==0 and r["model_gui_network_runtime_task_input"]==0
print("INDEPENDENT_AUDIT_PASS",r["rows_sha256"])
