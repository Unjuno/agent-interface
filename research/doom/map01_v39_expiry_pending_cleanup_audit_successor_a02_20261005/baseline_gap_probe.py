import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = json.loads((HERE / "candidate-a02-frozen.json").read_text(encoding="utf-8"))
OLD = HERE / "audit_successor_v1.py"
NEW = HERE / "audit_successor_v2.py"
CASES = {
    "authority_true": lambda d: next(e for e in d["events"] if e["event"] == "input_release_measurement").update(grants_input_authority=True),
    "edge_down": lambda d: next(e for e in d["events"] if e["event"] == "input_release_measurement").update(edge="down"),
    "reason_cancelled": lambda d: next(e for e in d["events"] if e["event"] == "input_release_measurement").update(reason="cancelled"),
}

def invoke(auditor, mutate, optimized):
    data = copy.deepcopy(RAW)
    mutate(data)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = root / "results" / "formal_02"
        out.mkdir(parents=True)
        (out / "candidate.json").write_text(json.dumps(data), encoding="utf-8")
        shutil.copyfile(auditor, root / "audit_a02.py")
        cmd = [sys.executable]
        if optimized:
            cmd.append("-O")
        cmd.append("audit_a02.py")
        return subprocess.run(cmd, cwd=root, capture_output=True, text=True)

result = {}
for name, mutate in CASES.items():
    result[name] = {}
    for optimized in (False, True):
        old = invoke(OLD, mutate, optimized)
        new = invoke(NEW, mutate, optimized)
        result[name]["optimized" if optimized else "normal"] = {
            "predecessor_exit": old.returncode,
            "successor_exit": new.returncode,
            "predecessor_false_accept": old.returncode == 0,
            "successor_rejected": new.returncode != 0,
        }
        if old.returncode != 0 or new.returncode == 0:
            raise SystemExit(f"gap differential failed: {name}, optimized={optimized}")
print(json.dumps(result, sort_keys=True))
