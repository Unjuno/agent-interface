import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
PARENT=ROOT.parent/"generation_bound_evidence_container_successor_2166_v1"/"experiment.py"
def main():
    p=json.loads((ROOT/"RESULT.json").read_text(encoding="utf-8")); v=json.loads((ROOT/"PROVENANCE.json").read_text(encoding="utf-8")); m=json.loads((ROOT/"SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    assert p["decision"]=="PASS_CONTAINER_REVALIDATION_SCOPED"
    assert p["statuses"]==["ENCODED","OBSOLETE","CACHE_HIT","ENCODED"]
    assert p["stale_control"]==p["reuse_control"]==p["provenance_control"]=="PASS"
    assert p["model"]==p["x11"]==p["input"]==0
    assert m["parent_path"]=="research/analysis/generation_bound_evidence_container_successor_2166_v1/experiment.py"
    assert subprocess.check_output(["git","hash-object",str(REPO/m["parent_path"])],text=True).strip()==m["parent_blob_sha"]
    assert hashlib.sha256(PARENT.read_bytes()).hexdigest()==v["source_sha256"]
    assert hashlib.sha256((ROOT/"RESULT.json").read_bytes()).hexdigest()==v["result_sha256"]
    assert v["parent_blob_sha"]==m["parent_blob_sha"] and v["parent_path"]==m["parent_path"]
    assert v["image_digest"].startswith("python@sha256:") and v["stdout"].strip()
    assert v["independent_audit"]=="PASS" and v["model"]==v["x11"]==v["input"]==0
    print("INDEPENDENT_AUDIT_PASS_PROVENANCE_COMPLETE")
if __name__=="__main__": main()
