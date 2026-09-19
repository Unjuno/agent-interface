import unittest
from pathlib import Path
import sys

from PIL import Image

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0,str(HERE))
from research.live_control.scoped_target_handle_v1 import TargetHandleStore
from research.live_control.target_handle_semantic_binding_v1 import (
    derive_contract, repair_contract)
from research.live_control.target_relative_crop_semantic_probe_v1 import score_path


ROOT=HERE
FORM=ROOT/"results/target-relative-semantic-probe-live-02/009.png"
SUCCESS=ROOT/"results/chromium-semantic-probe-transfer-live-02/012.png"
DIGEST="879ad35b666f63b1c9a401c359bd563c52170146b3e4ca5c7314448fdfb5784c"
RELATION={"schema":"target-semantic-region-relation-v1",
          "anchor":"target_box_origin","offset":[-235,-64],"size":[315,45]}


def observation(sequence, geometry):
    return {"sequence":sequence,"capture_ns":sequence*1_000_000,
        "pointer_binding":{"focus":8388611,"surface":8388611,
                           "geometry":list(geometry)}}


class TargetHandleSemanticBindingTests(unittest.TestCase):
    def setUp(self):
        self.store=TargetHandleStore("semantic-fixture",lambda:"save-handle")
        self.image=Image.open(FORM).convert("RGB")
        self.source=observation(1,[10,10,1050,780])
        self.mint=self.store.mint("save_form","window_content",[250,234,42,18],
            self.source,self.image,1_000_001,ttl_ms=1000,freshness_ms=100,search_radius=0)
        self.resolution=self.store.resolve_point("save-handle",[20,9],self.source,
            self.image,1_000_002)

    def tearDown(self): self.image.close()

    def test_derives_expected_window_content_box(self):
        result=derive_contract("submission","submission_heading",self.mint,
            self.resolution,self.source,RELATION,DIGEST,"submission_visible")
        self.assertEqual(result["contract"]["box_in_frame"],[5,160,320,205])
        self.assertEqual(result["receipt"]["resolved_semantic_screen_box"],
                         [15,170,330,215])
        self.assertFalse(result["receipt"]["grants_input_authority"])

    def test_resize_refuses_old_then_repairs_from_same_handle(self):
        initial=derive_contract("submission","submission_heading",self.mint,
            self.resolution,self.source,RELATION,DIGEST,"submission_visible")
        resized=observation(2,[10,10,930,780])
        resolution=self.store.resolve_point("save-handle",[20,9],resized,
            self.image,2_000_001)
        self.assertTrue(resolution["eligible"])
        self.assertEqual(score_path(initial["contract"],SUCCESS,resized["pointer_binding"])
                         ["reason"],"surface_size_changed")
        repaired=repair_contract(initial["contract"],self.mint,resolution,resized,RELATION)
        self.assertEqual(repaired["contract"]["source_geometry"],[10,10,930,780])
        self.assertTrue(score_path(repaired["contract"],SUCCESS,
                                   resized["pointer_binding"])["success"])
        self.assertEqual(repaired["receipt"]["model_calls"],0)

    def test_missing_handle_cannot_repair(self):
        initial=derive_contract("submission","submission_heading",self.mint,
            self.resolution,self.source,RELATION,DIGEST,"submission_visible")
        missing=self.store.resolve_point("absent",[20,9],observation(2,[10,10,930,780]),
                                         self.image,2_000_001)
        with self.assertRaises(ValueError):
            repair_contract(initial["contract"],self.mint,missing,
                            observation(2,[10,10,930,780]),RELATION)


if __name__=="__main__":unittest.main()
