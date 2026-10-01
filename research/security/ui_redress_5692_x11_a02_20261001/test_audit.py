import base64, copy, hashlib, unittest
from independent_audit import EXPECTED, audit

def crop(data):
 return {"base64":base64.b64encode(data).decode(),"sha256":hashlib.sha256(data).hexdigest(),"format":"X11_ZPixmap_raw","width":2,"height":2}

def fixture():
 rows=[]
 for (cond,policy),(admit,target_check,recipient) in EXPECTED.items():
  target={"pid":100,"window_id":10,"entry_id":11}; overlay=None
  if cond=="visible": overlay={"pid":200,"window_id":20,"mode":"visible","input_shape":True,"mapped":True}
  elif cond in ("transparent-input","race-after-check"): overlay={"pid":200,"window_id":20,"mode":"input","input_shape":True,"mapped":True}
  elif cond=="input-transparent": overlay={"pid":200,"window_id":20,"mode":"empty-input","input_shape":False,"mapped":True}
  same=cond!="visible"; before=crop(b"aaaa"); after=copy.deepcopy(before if same else crop(b"bbbb")); te=[]; oe=[]
  if recipient=="target": te=[{"type":"ButtonPress"},{"type":"ButtonRelease"}]
  elif recipient=="overlay": oe=[{"type":"ButtonPress"},{"type":"ButtonRelease"}]
  rows.append({"condition":cond,"policy":policy,"target":target,"overlay":overlay,"before_crop":before,"after_crop":after,
   "visual_same":same,"precheck_child_id":20 if overlay else 10,"recipient_is_target_at_precheck":target_check,
   "admitted":admit,"click_delivered":admit,"target_events":te,"overlay_events":oe})
 return {"schema":"ui-redress-5692-t0-raw-v1","rows":rows}

class Tests(unittest.TestCase):
 def test_pristine(self): self.assertEqual(audit(fixture())["disposition"],"METHOD_PASS_SCOPED")
 def test_pixel_digest(self):
  d=fixture(); d["rows"][0]["after_crop"]["base64"]="YmJiYg=="; self.assertTrue(audit(d)["errors"])
 def test_visual_mismatch(self):
  d=fixture(); d["rows"][4]["visual_same"]=False; self.assertTrue(audit(d)["errors"])
 def test_wrong_admission(self):
  d=fixture(); d["rows"][5]["admitted"]=True; self.assertTrue(audit(d)["errors"])
 def test_missing_foreign_press(self):
  d=fixture(); d["rows"][4]["overlay_events"]=[]; self.assertTrue(audit(d)["errors"])
 def test_input_transparent_control(self):
  d=fixture(); d["rows"][7]["target_events"]=[]; self.assertTrue(audit(d)["errors"])
 def test_visible_force_probe(self):
  d=fixture(); d["rows"][8]["overlay_events"]=[]; self.assertTrue(audit(d)["errors"])
 def test_race_redirect(self):
  d=fixture(); d["rows"][9]["overlay_events"]=[]; self.assertTrue(audit(d)["errors"])
 def test_duplicate(self):
  d=fixture(); d["rows"].append(copy.deepcopy(d["rows"][0])); self.assertTrue(audit(d)["errors"])

if __name__=="__main__": unittest.main()
