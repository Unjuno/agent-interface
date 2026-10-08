from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent.parent
REPO=HERE.parents[3]
if str(REPO) not in sys.path: sys.path.insert(0,str(REPO))
A02=HERE.parent/"a02-retained-screenshot-grounding"
from runtime.guarded_x11_v1.handles import TargetHandleStore
from runtime.guarded_x11_v1.handles_texture import FlatTargetRefused
CASES=json.loads((HERE/"INPUTS.json").read_text(encoding="utf-8"))["cases"]
NOW_NS=2_000_000


def observe(sequence,capture_ns,size):
    return {"sequence":sequence,"capture_ns":capture_ns,"pointer_binding":{"focus":101,"surface":202,"geometry":[0,0,size[0],size[1]]}}


def replay(case,padding,changed=False):
    with Image.open(A02/case["image_file"]) as f: image=f.convert("RGB")
    x0,y0,x1,y1=case["value_crop_xyxy"]
    box=[x0-padding,y0-padding,x1-x0+2*padding,y1-y0+2*padding]
    x,y=case["field_point"]
    offset=[x-box[0],y-box[1]]
    store=TargetHandleStore("a03-context-crop",id_factory=lambda:"private")
    try:
        minted=store.mint("field_context","window_content",box,observe(1,1_000_000,image.size),image,NOW_NS,ttl_ms=300_000,freshness_ms=1_500,search_radius=0,allowed_transformations=("window_translation",))
    except FlatTargetRefused:
        return {"status":"FLAT_REFUSED","eligible":False,"registry_entries":len(store._entries)}
    fresh=image.copy()
    if changed:
        ImageDraw.Draw(fresh).rectangle((box[0],box[1],box[0]+box[2]-1,box[1]+box[3]-1),fill=(255,255,255))
    resolved=store.resolve_point(minted["handle"],offset,observe(2,NOW_NS,fresh.size),fresh,NOW_NS+1_000_000)
    return {"status":resolved["status"],"eligible":resolved["eligible"],"point":resolved.get("point"),"registry_entries":len(store._entries)}


class ContextCropTargetHandleTests(unittest.TestCase):
    def test_four_pixel_context_padding_admits_every_retained_field(self):
        results=[replay(case,4) for case in CASES]
        self.assertEqual(results,[{"status":"VALID","eligible":True,"point":case["field_point"],"registry_entries":1} for case in CASES])

    def test_four_pixel_context_patch_change_refuses_every_handle(self):
        results=[replay(case,4,changed=True) for case in CASES]
        self.assertEqual(results,[{"status":"MISSING","eligible":False,"point":None,"registry_entries":1} for _ in CASES])


if __name__=="__main__": unittest.main(verbosity=2)
