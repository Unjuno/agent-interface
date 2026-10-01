"""Read-only publication check; no formal simulation invocation."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from restore import restore

ROOT=Path(__file__).resolve().parent
if __name__=="__main__":
    manifest=json.loads((ROOT/"MANIFEST.json").read_text())
    for name,digest in manifest.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise ValueError("publication hash:"+name)
    receipt=json.loads((ROOT/"formal01/EXECUTION.json").read_text())
    if receipt["returncode"]!=0 or receipt["timeout"] is not False or (ROOT/"formal01/OUTER.exit").read_text().strip()!="0":
        raise ValueError("formal execution receipt")
    for name in ("AUDIT","CONTROLS"):
        prior=json.loads((ROOT/f"formal01/{name}_EXECUTION.json").read_text())
        if prior["returncode"]!=0 or prior["stdout_sha256"]!=hashlib.sha256((ROOT/f"formal01/{name}.json").read_bytes()).hexdigest():
            raise ValueError("audit/control execution receipt")
    with tempfile.TemporaryDirectory(prefix="score4356-verify-") as tmp:
        target=Path(tmp)/"RAW.json"
        record=restore(target)
        for script,name in (("audit.py","AUDIT"),("controls.py","CONTROLS")):
            result=subprocess.run([sys.executable,"-S","-B",str(ROOT/script),str(target)],cwd=ROOT,capture_output=True,timeout=30)
            if result.returncode!=0 or result.stderr or result.stdout!=(ROOT/f"formal01/{name}.json").read_bytes():
                raise ValueError("re-audit differs:"+name)
        print(json.dumps({"status":"PASS_EXACT_RESTORATION_AND_REAUDIT","raw":record,"formal_reruns":0},sort_keys=True))
