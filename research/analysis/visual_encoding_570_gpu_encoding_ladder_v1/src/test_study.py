from __future__ import annotations
import base64, hashlib, json, tempfile, unittest
from pathlib import Path
from audit import audit, source_box

ARMS=["RAW","BORDER_RULER","COARSE_GRID","CONTEXT_CROP","GRID_CONTEXT"]
MODEL="qwen2.5vl:3b"; DIGEST="fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1"
def sha(b): return hashlib.sha256(b).hexdigest()

class StudyTests(unittest.TestCase):
    def fixture(self,root):
        (root/"data").mkdir(); (root/"formal").mkdir(); prompt="frozen"; cases=[]; samples=[]; n=0
        for j in range(12):
            srcid=f"case-{j:02d}"; source=f"source-{j}".encode(); (root/"data"/f"{srcid}.png").write_bytes(source); positive=j<10; target=[100,100,200,200] if positive else None
            for arm in ARMS:
                cid=f"{srcid}-{arm.lower()}"; image=f"image-{cid}".encode(); (root/"data"/f"{cid}.png").write_bytes(image)
                mapping={"kind":"identity"}
                if arm=="CONTEXT_CROP": mapping={"kind":"crop_resize","crop":[40,130,1240,700],"paste_xy":[40,58],"resized_wh":[1200,684]}
                if arm=="GRID_CONTEXT": mapping={"kind":"crop_resize","crop":[40,130,1240,700],"paste_xy":[40,130],"resized_wh":[1200,570],"grid_step_px":200}
                case={"case_id":cid,"source_case_id":srcid,"seed":2000+j,"present":positive,"target_box":target,"arm":arm,"source_path":f"{srcid}.png","source_sha256":sha(source),"image_path":f"{cid}.png","image_sha256":sha(image),"mapping":mapping,"width":1280,"height":800}; cases.append(case)
                result={"present":positive,"box":target}; request={"model":MODEL,"messages":[{"role":"user","content":prompt,"images":[base64.b64encode(image).decode()]}],"format":{},"stream":False,"keep_alive":"5m","options":{"temperature":0,"seed":case["seed"],"num_predict":128}}
                rec={"case_id":cid,"source_case_id":srcid,"arm":arm,"seed":case["seed"],"model":MODEL,"expected_digest":DIGEST,"request":request,"request_sha256":sha(json.dumps(request,sort_keys=True,separators=(",",":")).encode()),"image_sha256":sha(image),"source_sha256":sha(source),"mapping":case["mapping"],"started_utc_ns":n*100+10,"ended_utc_ns":n*100+20,"response":{"message":{"content":json.dumps(result)}},"error":None}
                (root/"formal"/(cid+".json")).write_text(json.dumps(rec)); samples.append({"utc_ns":n*100+15,"memory_used_mib":400,"ollama_ps_stdout":"qwen 100% GPU"}); n+=1
        (root/"data"/"PREFORMAL.json").write_text(json.dumps({"allocation":"test","prompt":prompt,"formal_cases":cases})); (root/"baseline.json").write_text(json.dumps({"memory_used_mib":100})); (root/"sampler.jsonl").write_text("\n".join(json.dumps(x) for x in samples))

    def test_context_crop_coordinate_roundtrip(self):
        mapping={"kind":"crop_resize","crop":[40,130,1240,700],"paste_xy":[40,58],"resized_wh":[1200,684]}
        src=[475,238,805,355]; pres=[40+(src[0]-40),58+(src[1]-130)*1.2,40+(src[2]-40),58+(src[3]-130)*1.2]
        self.assertEqual(source_box([round(x) for x in pres],mapping),src)

    def test_complete_five_arm_raw_audit(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.fixture(root); result=audit(root)
            self.assertEqual(result["decision"],"REJECT_NO_MATERIAL_ENCODING_GAIN")
            self.assertEqual(result["errors"],[]); self.assertEqual(result["arms"]["RAW"]["positive_hits"],10)

    def test_request_image_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.fixture(root); p=root/"formal"/"case-00-raw.json"; r=json.loads(p.read_text()); r["request"]["messages"][0]["images"][0]=base64.b64encode(b"mutated").decode(); p.write_text(json.dumps(r))
            self.assertIn("request_image:case-00-raw",audit(root)["errors"])

    def test_source_pixel_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.fixture(root); (root/"data"/"case-00.png").write_bytes(b"changed")
            self.assertIn("source_hash:case-00-raw",audit(root)["errors"])

    def test_mapping_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.fixture(root); p=root/"formal"/"case-00-context_crop.json"; r=json.loads(p.read_text()); r["mapping"]["paste_xy"]=[41,58]; p.write_text(json.dumps(r))
            self.assertIn("case_binding:case-00-context_crop",audit(root)["errors"])

    def test_malformed_response_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.fixture(root); p=root/"formal"/"case-00-raw.json"; r=json.loads(p.read_text()); r["response"]["message"]["content"]="{\"present\":true}"; p.write_text(json.dumps(r))
            self.assertIn("schema:case-00-raw",audit(root)["errors"])

    def test_missing_raw_row_is_detected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.fixture(root); (root/"formal"/"case-00-raw.json").unlink()
            self.assertIn("missing:case-00-raw",audit(root)["errors"])

    def test_missing_gpu_placement_holds(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); self.fixture(root); rows=[json.loads(x) for x in (root/"sampler.jsonl").read_text().splitlines()]
            for row in rows: row["memory_used_mib"]=100; row["ollama_ps_stdout"]="qwen 100% CPU"
            (root/"sampler.jsonl").write_text("\n".join(json.dumps(x) for x in rows)); self.assertEqual(audit(root)["decision"],"HOLD_AUDIT_OR_GPU_GATE")

if __name__=="__main__": unittest.main(verbosity=2)
