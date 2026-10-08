"""Run the frozen dispatch check in normal and optimized Python."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "run.py"
AUDIT_PATH = HERE / "audit.py"
spec = importlib.util.spec_from_file_location("dispatch_audit", AUDIT_PATH)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
outputs = {}
for mode, optimize in (("normal", []), ("optimized", ["-O"])):
    proc = subprocess.run([sys.executable, *optimize, "-B", str(RUN)], capture_output=True, text=True)
    outputs[mode] = {"exit_code": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
    if proc.returncode:
        raise SystemExit(f"{mode} candidate failed: {proc.stderr}")
if outputs["normal"]["stdout"] != outputs["optimized"]["stdout"]:
    raise SystemExit("normal/optimized outputs differ")
result = json.loads(outputs["normal"]["stdout"])
audit_result = audit.audit_result(result)
if audit_result["status"] != "PASS_DISPATCH_CONSTRUCTION":
    raise SystemExit(f"independent audit failed: {audit_result}")
retained_result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
retained_audit = json.loads((HERE / "AUDIT.json").read_text(encoding="utf-8"))
if outputs["normal"]["stdout"] != (HERE / "normal.stdout").read_text(encoding="utf-8").strip():
    raise SystemExit("candidate output differs from retained normal raw")
if outputs["optimized"]["stdout"] != (HERE / "optimized.stdout").read_text(encoding="utf-8").strip():
    raise SystemExit("optimized output differs from retained optimized raw")
if result != retained_result or audit_result != retained_audit:
    raise SystemExit("reproduction differs from retained result or audit")
for field, value in (("modes", "mutated"), ("instrumentation_chain", "mutated")):
    changed = json.loads(json.dumps(result))
    changed[field] = value
    if audit.audit_result(changed)["status"] != "FAIL_DISPATCH_CONSTRUCTION":
        raise SystemExit(f"audit accepted mutated {field}")
print(json.dumps({"normal_exit": outputs["normal"]["exit_code"], "optimized_exit": outputs["optimized"]["exit_code"],
                  "byte_identical": True, "audit": audit_result["status"],
                  "mutation_controls": 2, "disposition": result["disposition"]}, sort_keys=True))
