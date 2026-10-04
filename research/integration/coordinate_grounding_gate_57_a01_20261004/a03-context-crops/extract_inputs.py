from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
REF="e8f7c02cb98d849312a4889fa4d52ec424088732"
A14="research/integration/compiled_gui_bundle_57_20261004/a14-lifecycle-cross-task-construction"
PR="research/integration/planner_contract_56_4d74_20261004/r02/formal-output/block-2/C"
A02=HERE.parent/"a02-retained-screenshot-grounding"


def source(path):
    oid=subprocess.run(["git","rev-parse",f"{REF}:{path}"],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
    raw=subprocess.run(["git","cat-file","blob",oid],cwd=ROOT,check=True,capture_output=True).stdout
    return oid,raw

manifest={"schema":"a03-context-crop-inputs-v1","source_pr_head":REF,"source_runtime_main_snapshot":"02953aa83d62e69a787de7732bf172f3f8ef8e1c","source_main_tip_checked":"4c2fe6cbd4218306bcb203cf04258b0f9a322213","cases":[]}
for task,name in [(2,"029.png"),(3,"054.png"),(4,"079.png"),(5,"105.png"),(6,"134.png")]:
    answer_path=f"{A14}/task-{task}/answer.json"
    prompt_path=f"{A14}/task-{task}/PROMPT.txt"
    answer_oid,answer_raw=source(answer_path)
    prompt_oid,prompt_raw=source(prompt_path)
    answer=json.loads(answer_raw)
    image_path=f"{PR}/client/runtime/{name}"
    image_oid,image_raw=source(image_path)
    fixture=A02/"inputs"/name
    assert hashlib.sha256(fixture.read_bytes()).hexdigest()==hashlib.sha256(image_raw).hexdigest()
    manifest["cases"].append({"task":task,"image_file":f"../a02-retained-screenshot-grounding/inputs/{name}","image_source_path":image_path,"image_git_blob":image_oid,"image_sha256":hashlib.sha256(image_raw).hexdigest(),"answer_source_path":answer_path,"answer_git_blob":answer_oid,"answer_sha256":hashlib.sha256(answer_raw).hexdigest(),"prompt_source_path":prompt_path,"prompt_git_blob":prompt_oid,"prompt_sha256":hashlib.sha256(prompt_raw).hexdigest(),"field_point":answer["field_point"],"value_crop_xyxy":answer["value_crop"]})
(HERE/"INPUTS.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
print(json.dumps({"cases":len(manifest["cases"]),"source_pr_head":REF,"screenshot_bytes_reused":sum((A02/"inputs"/c["image_file"].split("/")[-1]).stat().st_size for c in manifest["cases"])}))
