from unittest.mock import patch
import hashlib, json
from pathlib import Path
import sys
for parent in Path(__file__).resolve().parents:
    if (parent / "make_dataset.py").is_file():
        sys.path.insert(0,str(parent))
        break
else:
    raise RuntimeError("prepared #5139 source package not found")
import make_dataset
from joint_selector import select_support_joint
from independent_audit import audit_document

FORMAL_SEED_SENTINEL_ONLY=990000017
summaries=[]; heldout_digests=set(); raw_bytes=None
for support_seed in range(1,129):
    with patch.object(make_dataset,"select_support",select_support_joint):
        document=make_dataset.build(FORMAL_SEED_SENTINEL_ONLY,support_seed,"HOST_CONSTRUCTION_SENTINEL_ONLY")
    errors=audit_document(document)
    assert errors==[],(support_seed,errors)
    canonical=json.dumps(document["heldout"],sort_keys=True,separators=(",",":" )).encode("utf-8")
    heldout_digests.add(hashlib.sha256(canonical).hexdigest())
    if support_seed==1:
        raw_bytes=(json.dumps(document,sort_keys=True,separators=(",",":"))+"\n").encode("utf-8")
    summaries.append({"support_seed":support_seed,"imbalanced_rows":len(document["supports"]["imbalanced"]),"balanced_rows":len(document["supports"]["balanced"]),"audit_errors":len(errors)})
assert len(heldout_digests)==1,heldout_digests
assert all(x["imbalanced_rows"]==32 and x["balanced_rows"]==32 and x["audit_errors"]==0 for x in summaries)
raw_path=Path(__file__).resolve().parent/"construction_sentinel_1.json"
raw_path.write_bytes(raw_bytes)
print(json.dumps({"status":"PASS_FULL_BUILDER_JOINT_MATCHED_CONSTRUCTION_ONLY","runs":len(summaries),"all_independent_audits_pass":True,"shared_heldout_digest_across_support_seeds":next(iter(heldout_digests)),"sentinel_raw_sha256":hashlib.sha256(raw_bytes).hexdigest(),"sentinel_raw_bytes":len(raw_bytes),"formal_seed":FORMAL_SEED_SENTINEL_ONLY,"formal_seed_is_allocation":False,"limitations":["Uses synthetic sentinels only and host CPython; no model, GPU, CUDA, Docker, LoRA fit, or formal allocation.","Candidate selector is injected at the builder boundary; make_dataset.py and default sampler are unchanged.","Independent audit reconstructs selection without importing candidate selector or candidate rank function.","The 16-vs-4 set arms use the same four joint cells but differ by row identity and 1-vs-4 multiplicity.","Prepared source branch is stale relative to current main and requires fresh freeze before formal use."]},sort_keys=True))


