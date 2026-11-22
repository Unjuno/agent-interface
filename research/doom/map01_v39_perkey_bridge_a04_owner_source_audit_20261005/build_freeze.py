from __future__ import annotations
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCES=[".gitattributes","README.md","audit_a04.py","test_a04_audit.py","build_freeze.py"]+[p.relative_to(HERE).as_posix() for p in sorted((HERE/"SOURCE").rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.suffix!=".pyc"]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 f={"schema":"map01_v39_perkey_bridge_a04_owner_source_audit_freeze_v1","run_id":"v39-perkey-bridge-a04-owner-source-audit-20261005","H":"A projected V39 release is justified only by a matching confirmed per-key up row in the retained raw owner stream.","T":"Raw-only audit of the exact retained A03 raw/result; exercise removal and invalidation mutations without candidate rerun.","D":"PASS only if original raw passes, prior audit accepts both mutations, and successor rejects both.","C":"Audit-only successor; original A02/A03 candidate evidence remains byte-identical.","U":"One retained fake-display trace; no live V39 deployment, GUI, OS input, game, model, application effect, or benefit claim.","source_run_id":json.loads((HERE/"SOURCE/BRIDGE/RAW_A03.json").read_text())["run_id"],"input_sha256":sha(HERE/"SOURCE/BRIDGE/RAW_A03.json"),"result_sha256":sha(HERE/"SOURCE/BRIDGE/RESULT_A03.json"),"source_sha256":{p:sha(HERE/p) for p in SOURCES},"scope":"raw owner-stream source join and confirmed-up bracket audit"}
 (HERE/"FREEZE.json").write_text(json.dumps(f,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
 print(json.dumps(f,sort_keys=True))
if __name__=="__main__":main()
