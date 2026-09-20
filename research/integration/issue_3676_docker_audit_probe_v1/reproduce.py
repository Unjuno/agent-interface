import copy, hashlib, importlib.util, json, pathlib, subprocess, sys, tempfile

# /input contains the immutable #3675 source/evidence; /probe contains this script.
root = pathlib.Path("/input")
probe = pathlib.Path(__file__).resolve().parent
source = root / "src" / "audit.py"
raw_path = root / "artifacts/formal_01/raw.json"
freeze_path = root / "FREEZE.json"
audit_path = root / "artifacts/formal_01/audit.json"

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

spec = importlib.util.spec_from_file_location("frozen_audit", source)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
raw = json.loads(raw_path.read_text())
mutations = {}
x = copy.deepcopy(raw); x["events"].append({"event":"unexpected"}); mutations["unexpected_event"] = x
x = copy.deepcopy(raw); x["events"].insert(4, copy.deepcopy(next(e for e in x["events"] if e.get("event")=="stale_admission"))); mutations["duplicate_stale"] = x
x = copy.deepcopy(raw); next(e for e in x["events"] if e.get("event")=="stale_admission")["would_call_bridge"] = True; mutations["contradictory_bridge"] = x
x = copy.deepcopy(raw); x["events"][2],x["events"][3] = x["events"][3],x["events"][2]; mutations["reordered_transitions"] = x
x = copy.deepcopy(raw); x["events"][0]["unexpected_field"] = True; mutations["unsupported_field"] = x
result = {"raw_sha256":digest(raw_path),"freeze_sha256":digest(freeze_path),"audit_source_sha256":digest(source),"original_audit_sha256":digest(audit_path),"baseline_errors":audit.errors_for(raw),"mutations":{k:audit.errors_for(v) for k,v in mutations.items()}}
with tempfile.TemporaryDirectory() as tmp:
    cli = subprocess.run([sys.executable,str(source),str(raw_path),"--freeze",str(freeze_path),"--output",str(pathlib.Path(tmp)/"audit.json")],capture_output=True,text=True)
result["cli"]={"exit_code":cli.returncode,"stdout":cli.stdout,"stderr":cli.stderr}
print(json.dumps(result,indent=2,sort_keys=True))
if result["baseline_errors"] or any(result["mutations"].values()) or result["cli"]["exit_code"] != 1: raise SystemExit(2)
