from __future__ import annotations
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 freeze=json.loads((HERE/"FREEZE.json").read_text())
 result=json.loads((HERE/"RESULT.json").read_text())
 receipt=json.loads((HERE/"RUN_RECEIPT.json").read_text())
 errors=[]
 for rel,expected in freeze["source_sha256"].items():
  path=HERE/rel
  if not path.is_file() or digest(path)!=expected:
   errors.append("SOURCE_HASH_MISMATCH:"+rel)
 for rel,expected in result["candidate_source_sha256"].items():
  path=HERE/rel
  if not path.is_file():
   errors.append("CANDIDATE_MISSING:"+rel)
  elif digest(path)!=expected:
   errors.append("CANDIDATE_HASH_MISMATCH:"+rel)
 if result["status"]!="PASS_DETERMINISTIC_RACE_FIXED":
  errors.append("RESULT_STATUS")
 for mode in ("normal","optimized"):
  if result[mode]["passed"]!=5 or result[mode]["failed"]!=0:
   errors.append("RESULT_COUNTS:"+mode)
 for run in receipt["commands"]:
  if run["exit_code"]!=0 or run["tests_passed"]!=5 or run["tests_failed"]!=0:
   errors.append("RUN_RECEIPT")
 manifest=HERE/"SHA256SUMS"
 listed={}
 for line in manifest.read_text().splitlines():
  expected,rel=line.split("  ",1);listed[rel]=expected
 for rel,expected in listed.items():
  path=HERE/rel
  if rel=="SHA256SUMS" or not path.is_file() or digest(path)!=expected:
   errors.append("MANIFEST_MISMATCH:"+rel)
 actual={p.relative_to(HERE).as_posix() for p in HERE.rglob("*")
         if p.is_file() and p!=manifest and "__pycache__" not in p.parts and p.suffix!=".pyc"}
 if set(listed)!=actual:
  errors.append("MANIFEST_COVERAGE")
 print(json.dumps({"status":"PASS_AUDIT" if not errors else "FAIL_AUDIT",
                   "listed_files":len(listed),"source_files":len(freeze["source_sha256"]),
                   "errors":errors},sort_keys=True))
 raise SystemExit(bool(errors))
if __name__=="__main__":main()
