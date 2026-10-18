from __future__ import annotations
import hashlib,json,subprocess,sys
from pathlib import Path
from PIL import Image,ImageStat

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
A02=HERE.parent/"a02-retained-screenshot-grounding"
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
FREEZE=json.loads((HERE.parent/"FREEZE.json").read_text(encoding="utf-8"))
INPUTS=json.loads((HERE/"INPUTS.json").read_text(encoding="utf-8"))
RESULT=json.loads((HERE/"RESULT.json").read_text(encoding="utf-8"))

def blob_bytes(oid):
    return subprocess.run(["git","cat-file","blob",oid],cwd=ROOT,check=True,capture_output=True).stdout

def source_blob(commit,path):
    return subprocess.run(["git","rev-parse",f"{commit}:{path}"],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()

def independent_box(case,image,padding):
    x0,y0,x1,y1=case["value_crop_xyxy"]
    x,y=case["field_point"]
    left=max(x0-padding,x-48,0); top=max(y0-padding,y-48,0)
    right=min(x1+padding,x+48,image.width); bottom=min(y1+padding,y+48,image.height)
    return [left,top,right-left,bottom-top]

for path,record in FREEZE["sources"].items():
    assert source_blob(FREEZE["source_commit"],path)==record["git_blob"]
    assert source_blob(INPUTS["source_main_tip_checked"],path)==record["git_blob"]

assert INPUTS["source_pr_head"]=="e8f7c02cb98d849312a4889fa4d52ec424088732"
expected=[]
for case in INPUTS["cases"]:
    image_data=(HERE/case["image_file"]).resolve().read_bytes()
    assert hashlib.sha256(image_data).hexdigest()==case["image_sha256"]
    assert hashlib.sha256(blob_bytes(case["image_git_blob"])).hexdigest()==case["image_sha256"]
    answer_raw=blob_bytes(case["answer_git_blob"])
    assert hashlib.sha256(answer_raw).hexdigest()==case["answer_sha256"]
    answer=json.loads(answer_raw)
    assert answer["field_point"]==case["field_point"] and answer["value_crop"]==case["value_crop_xyxy"]
    prompt_raw=blob_bytes(case["prompt_git_blob"])
    assert hashlib.sha256(prompt_raw).hexdigest()==case["prompt_sha256"]
    assert b"exclude border/label" in prompt_raw and b"value_crop=[left,top,right,bottom]" in prompt_raw
    with Image.open(HERE/case["image_file"]) as f: image=f.convert("RGB")
    assert image.size==(1280,800)
    checks=[]
    for padding in (0,4):
        box=independent_box(case,image,padding)
        assert 4<=box[2]<=96 and 4<=box[3]<=96
        x,y=case["field_point"]
        assert box[0]<=x<box[0]+box[2] and box[1]<=y<box[1]+box[3]
        patch=image.crop((box[0],box[1],box[0]+box[2],box[1]+box[3]))
        std=max(ImageStat.Stat(patch).stddev)
        status="FLAT_REFUSED" if std<8 else "VALID"
        checks.append((box,round(std,6),status))
    # The exact same patch is present at the identical bound observation. With radius 0,
    # successful admission resolves VALID; replacing all region pixels prevents that match.
    padded_box,padded_std,_=checks[1]
    masked=image.copy()
    from PIL import ImageDraw
    ImageDraw.Draw(masked).rectangle((padded_box[0],padded_box[1],padded_box[0]+padded_box[2]-1,padded_box[1]+padded_box[3]-1),fill=(255,255,255))
    masked_patch=masked.crop((padded_box[0],padded_box[1],padded_box[0]+padded_box[2],padded_box[1]+padded_box[3]))
    assert masked_patch.tobytes()!=image.crop((padded_box[0],padded_box[1],padded_box[0]+padded_box[2],padded_box[1]+padded_box[3])).tobytes()
    expected.append({"task":case["task"],"raw":checks[0],"padded":checks[1],"changed_status":"MISSING"})

for row,expect in zip(RESULT["cases"],expected,strict=True):
    assert row["task"]==expect["task"]
    for key,entry in (("raw_crop",expect["raw"]),("padded_crop",expect["padded"])):
        assert row[key]["box"]==entry[0] and row[key]["max_channel_stddev"]==entry[1] and row[key]["status"]==entry[2]
    assert row["padded_crop_after_region_replacement"]["status"]==expect["changed_status"]
assert RESULT["summary"]=={"cases":5,"raw_crop_valid":0,"raw_crop_flat_refused":5,"padded_crop_valid":5,"padded_crop_changed_missing":5,"input_dispatch_count":0,"model_call_count":0,"gui_call_count":0}
stop=(HERE/"out/UNBOUNDED_CROP_STOP.txt").read_text(encoding="utf-8",errors="replace")
assert "handle region dimensions must be 4..96" in stop and "errors=2" in stop
print(json.dumps({"status":"PASS_A03_INPUT_PIXEL_AND_OUTCOME_AUDIT","frozen_runtime_sources":len(FREEZE["sources"]),"screenshots":len(INPUTS["cases"]),"raw_crop_refused":5,"padded_crop_valid":5,"changed_missing":5,"input_dispatch_count":0},sort_keys=True))
