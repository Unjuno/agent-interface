from __future__ import annotations
import hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCES=[".gitattributes","README.md","audit_a05.py","test_a05.py","build_freeze.py"]+[p.relative_to(HERE).as_posix() for p in sorted((HERE/"SOURCE/A04").rglob("*")) if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    freeze={"schema":"map01_v39_perkey_measurement_consumer_a05_freeze_v1","run_id":"MAP01-V39-PERKEY-MEASUREMENT-CONSUMER-A05-20261005","H":"A04 accepts JSON true as candidate invocation count 1; exact integer typing should reject the alias.","T":"Offline mutation audit of the exact retained A04 result; compare legacy and A05 behavior on JSON-compatible count values.","D":"PASS only if exact integer 1 passes, bool true is shown to pass A04 but fail A05, and false, zero, two, float, string, and null fail A05.","C":"Audit-only successor; preserves all A04 bytes and does not rerun its candidate.","U":"One audit metadata field only; no live input, GUI/game, application effect, feedback, recovery, threat response, or MAP01 result.","source_sha256":{name:sha(HERE/name) for name in SOURCES},"scope":"exact-type guard for retained A04 invocation-count metadata"}
    (HERE/"FREEZE.json").write_text(json.dumps(freeze,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(freeze,sort_keys=True))
if __name__=="__main__": main()
