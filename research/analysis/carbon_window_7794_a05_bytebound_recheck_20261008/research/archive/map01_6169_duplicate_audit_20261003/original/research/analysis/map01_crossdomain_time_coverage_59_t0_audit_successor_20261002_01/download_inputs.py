import hashlib
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
root = HERE / "inputs"
root.mkdir(exist_ok=True)
base = "https://raw.githubusercontent.com/Unjuno/agent-interface/"
for name, spec in freeze["inputs"].items():
    url = base + freeze["input_source_commit"] + "/" + spec["path"]
    request = urllib.request.Request(url, headers={"User-Agent": "r133-6164-audit-successor"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
    sha = hashlib.sha256(data).hexdigest()
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if sha != spec["sha256"] or blob != spec["git_blob_sha"]:
        raise SystemExit("STOP_INPUT_HASH_MISMATCH:" + name)
    (root / name).write_bytes(data)
# Candidate output is retained in the parent T0 branch; it is immutable audit input.
url = base + freeze["parent_pr"]["head_sha"] + "/research/analysis/map01_crossdomain_time_coverage_59_t0_20261002_01/candidate_result.json"
request = urllib.request.Request(url, headers={"User-Agent": "r133-6164-audit-successor"})
with urllib.request.urlopen(request, timeout=30) as response:
    data = response.read()
if hashlib.sha256(data).hexdigest() != freeze["parent_candidate_result_sha256"]:
    raise SystemExit("STOP_PARENT_CANDIDATE_HASH_MISMATCH")
(root / "candidate_result.json").write_bytes(data)
