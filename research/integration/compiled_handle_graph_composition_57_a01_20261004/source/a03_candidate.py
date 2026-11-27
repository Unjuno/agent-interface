from __future__ import annotations
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageStat

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
if str(REPO) not in sys.path: sys.path.insert(0,str(REPO))
A02=HERE.parent/"a02-retained-screenshot-grounding"
from runtime.guarded_x11_v1.handles import TargetHandleStore
from runtime.guarded_x11_v1.handles_texture import FlatTargetRefused
NOW_NS=2_000_000
PAD=4
MAX_DIM=96


def observation(sequence,capture_ns,size):
    return {"sequence":sequence,"capture_ns":capture_ns,"pointer_binding":{"focus":101,"surface":202,"geometry":[0,0,size[0],size[1]]}}


def bounded_box(case,image,padding):
    x0,y0,x1,y1=case["value_crop_xyxy"]
    x,y=case["field_point"]
    left=max(x0-padding,x-MAX_DIM//2,0)
    top=max(y0-padding,y-MAX_DIM//2,0)
    right=min(x1+padding,x+MAX_DIM//2,image.width)
    bottom=min(y1+padding,y+MAX_DIM//2,image.height)
    return [left,top,right-left,bottom-top]


def replay(case,padding,changed=False):
    with Image.open(A02/case["image_file"]) as f: image=f.convert("RGB")
    box=bounded_box(case,image,padding)
    x,y=case["field_point"]
    offset=[x-box[0],y-box[1]]
    patch=image.crop((box[0],box[1],box[0]+box[2],box[1]+box[3]))
    max_stddev=max(ImageStat.Stat(patch).stddev)
    store=TargetHandleStore("a03-context-crop",id_factory=lambda:"private")
    try:
        minted=store.mint("field_context","window_content",box,observation(1,1_000_000,image.size),image,NOW_NS,ttl_ms=300_000,freshness_ms=1_500,search_radius=0,allowed_transformations=("window_translation",))
    except FlatTargetRefused as exc:
        return {"box":box,"max_channel_stddev":round(max_stddev,6),"status":"FLAT_REFUSED","eligible":False,"reason":str(exc),"registry_entries":len(store._entries)}
    fresh=image.copy()
    if changed:
        ImageDraw.Draw(fresh).rectangle((box[0],box[1],box[0]+box[2]-1,box[1]+box[3]-1),fill=(255,255,255))
    resolved=store.resolve_point(minted["handle"],offset,observation(2,NOW_NS,fresh.size),fresh,NOW_NS+1_000_000)
    return {"box":box,"max_channel_stddev":round(max_stddev,6),"status":resolved["status"],"eligible":resolved["eligible"],"resolved_point":resolved.get("point"),"reason":resolved.get("reason"),"registry_entries":len(store._entries)}


def run_experiment():
    manifest=json.loads((HERE/"INPUTS.json").read_text(encoding="utf-8"))
    cases=[]
    for case in manifest["cases"]:
        raw=replay(case,0)
        padded=replay(case,PAD)
        changed=replay(case,PAD,changed=True)
        cases.append({"task":case["task"],"field_point":case["field_point"],"value_crop_xyxy":case["value_crop_xyxy"],"raw_crop":raw,"padded_crop":padded,"padded_crop_after_region_replacement":changed})
    summary={
        "cases":len(cases),
        "raw_crop_valid":sum(c["raw_crop"]["status"]=="VALID" for c in cases),
        "raw_crop_flat_refused":sum(c["raw_crop"]["status"]=="FLAT_REFUSED" for c in cases),
        "padded_crop_valid":sum(c["padded_crop"]["status"]=="VALID" for c in cases),
        "padded_crop_changed_missing":sum(c["padded_crop_after_region_replacement"]["status"]=="MISSING" for c in cases),
        "input_dispatch_count":0,"model_call_count":0,"gui_call_count":0,
    }
    return {"schema":"a03-context-crop-replay-v1","input_source_pr_head":manifest["source_pr_head"],"source_runtime_main_snapshot":manifest["source_runtime_main_snapshot"],"padding_px":PAD,"maximum_region_dimension_px":MAX_DIM,"cases":cases,"summary":summary,"interpretation":"offline pixel-patch identity experiment; not semantic target verification"}


if __name__=="__main__": print(json.dumps(run_experiment(),indent=2,sort_keys=True))
