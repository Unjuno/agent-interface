import hashlib, json, pathlib
ROOT=pathlib.Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def blob(p):
 b=p.read_bytes(); return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
m=json.loads((ROOT/"inputs/source-manifest.json").read_text())
checks=[]
for rel,meta in m["files"].items():
 p=ROOT/"inputs"/rel
 checks.append({"check":"sha256-and-size","path":rel,"pass":p.is_file() and p.stat().st_size==meta["bytes"] and sha(p)==meta["sha256"]})
for rel,expected in m["git_blob_ids"].items():
 checks.append({"check":"git-blob-id","path":rel,"pass":blob(ROOT/"inputs"/rel)==expected})
for name,expected in [("candidate-normal",("Ran 7 tests", "\nOK\n")),("candidate-optimized",("Ran 7 tests", "\nOK\n"))]:
 log=(ROOT/"raw"/(name+".log")).read_text(errors="replace")
 exit_code=(ROOT/"raw"/(name+".exit")).read_text().strip()
 checks.append({"check":name,"pass":all(x in log for x in expected) and exit_code=="exit=0"})
base=(ROOT/"raw/main-normal.log").read_text(errors="replace")
checks.append({"check":"main expected contrast","pass":"AssertionError" in base and "assert {node.name for node in FUNCTIONS} == NAMES" in base and (ROOT/"raw/main-normal.exit").read_text().strip()=="exit=1"})
result={"result":"PASS" if all(c["pass"] for c in checks) else "FAIL","checks":checks,"count":len(checks)}
(ROOT/"AUDIT.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
raise SystemExit(0 if result["result"]=="PASS" else 1)
