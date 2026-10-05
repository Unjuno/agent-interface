from __future__ import annotations
import hashlib,json,os
from pathlib import Path
from audit_a05_raw import SOURCE_SHA256,audit_document
def main():
    raw_path=Path(os.environ.get("A06_RAW_INPUT","/input/a05-candidate.raw.json"))
    raw_bytes=raw_path.read_bytes()
    digest=hashlib.sha256(raw_bytes).hexdigest()
    if digest != SOURCE_SHA256: raise ValueError(f"frozen raw SHA-256 mismatch: {digest}")
    document=json.loads(raw_bytes.decode("utf-8"))
    audit_document(document)
    result={"schema":"scorer-feedback-attribution-a06-candidate-audit-v1","status":"PASS_STRICT_RAW_AUDIT","input_sha256":digest,"cases_checked":len(document["cases"]),"expected_case_labels":[row["case"] for row in document["cases"]],"candidate_code_imported":False,"scope":"retained synthetic raw-output integrity only"}
    out=Path(os.environ.get("A06_OUT","/out/candidate.raw.json"))
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__": main()
