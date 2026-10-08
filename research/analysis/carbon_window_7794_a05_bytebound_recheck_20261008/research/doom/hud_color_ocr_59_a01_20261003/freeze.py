import datetime
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
names=["README.md","Dockerfile","build_inputs.py","candidate.py","auditor.py","run_stage.py","choose.py","challenge.py","capture.py","freeze.py"]
inspection=json.loads(json.loads((ROOT/"setup/image_inspect.json").read_text())["stdout"])[0]
base=json.loads(json.loads((ROOT/"setup/base_inspect.json").read_text())["stdout"])[0]
inputs={name:digest(ROOT/name) for name in ["TRUTH.json","input/pilot/manifest.json","input/evaluation/manifest.json"]}
for phase in ("pilot","evaluation"):
    for row in json.loads((ROOT/f"input/{phase}/manifest.json").read_text()):
        assert digest(ROOT/f"input/{phase}"/row["image"])==row["sha256"]
record={"created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"vm":"research-59-hud-ocr-5ce3-20261003","owner":"01a0b98b-5ce3-7f53-82f3-e09294f24d57","image_id":inspection["Id"],"base_repo_digests":base["RepoDigests"],"source_sha256":{name:digest(ROOT/name) for name in names},"input_sha256":inputs,"reference_events_sha256":"2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381","intake_main":"38518811f537a5dc3dea3b231036b9006b25d8aa","eligibility":{"exact_fraction_min":0.95,"wrong_nonempty_fraction_max":0.01,"gain_fraction_min":0.25}}
record["guest_study_path"]="/mnt/mac"+str(ROOT)
record["guest_source_path"]="/mnt/mac"+str(ROOT.parents[2]/"research/doom/results/map01-v39-coast-liveness-live-01/runtime")
with (ROOT/"FREEZE.json").open("x") as output: json.dump(record,output,indent=2); output.write("\n")
print(json.dumps({"image_id":record["image_id"],"source_files":len(names),"input_records":len(inputs)}))
