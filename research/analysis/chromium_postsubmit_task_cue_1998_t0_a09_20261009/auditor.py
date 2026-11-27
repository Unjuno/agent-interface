#!/usr/bin/env python3
"""Independent stdlib-only raw OCR, crop, task-oracle, and mutation audit."""
import base64,copy,hashlib,json,pathlib,re,sys
PKG=pathlib.Path(__file__).resolve().parent; ROOT=PKG.parents[2]
def sha(b): return hashlib.sha256(b).hexdigest()
def check(raw,f,a04,design,oracle,submitted,pilot,freeze_sha):
 errors=[]; expected={r["case_id"]:r for r in a04["rows"] if r["frame_id"]==f["frame_id"] and r["selected_kind"]=="FOCUSED_REGION"}
 frame=next((x for x in design["frames"] if x["frame_id"]==f["frame_id"]),None)
 if frame is None or frame.get("epoch")!=f["epoch"] or frame.get("first_action_id")!=f["action_id"] or frame.get("source_png_path")!=f["frame_png_path"]: errors.append("frame-provenance")
 rows=raw.get("rows",[]); ids=[r.get("case_id") for r in rows]
 if raw.get("schema")!="a09-ocr-output-v1" or raw.get("case_count")!=20 or len(rows)!=20: errors.append("coverage")
 if len(set(ids))!=20 or set(ids)!=set(expected): errors.append("case-identities")
 if raw.get("freeze_sha256")!=freeze_sha or raw.get("pilot_stdout_sha256")!=f["pilot_stdout_sha256"]: errors.append("freeze-or-pilot-identity")
 if oracle.get("goal",{}).get("token")!=f["target_token"] or oracle.get("oracle",{}).get("actual",{}).get("value")!=[f["target_token"]] or submitted.strip()!=f["submitted_expected"]: errors.append("task-oracle-binding")
 try: pilot_text=pilot.decode("utf-8","replace")
 except Exception: pilot_text=""
 if f["target_token"] in pilot_text: errors.append("pilot-was-not-a-miss")
 event=next((x for x in (json.loads(l) for l in (ROOT/f["ledger_path"]).read_text().splitlines()) if frame and x.get("sequence")==frame.get("ledger_sequence")),None)
 action=next((x for x in json.loads((ROOT/f["actions_path"]).read_text()) if x.get("action_id")==f["action_id"]),None)
 if event is None or event.get("action_id")!=f["action_id"] or event.get("sha256")!=frame.get("source_pixel_sha256") or action is None or action.get("public_effect_known_ns",0)<=event.get("observed_ns",0): errors.append("pending-effect-provenance")
 matches=[]
 for r in rows:
  src=expected.get(r.get("case_id"),{}); rel=f["a04_package"]+"/"+src.get("focus_png_path","")
  if r.get("png_path")!=rel or r.get("bounds")!=src.get("request",{}).get("bounds"): errors.append("crop-identity:"+str(r.get("case_id")))
  if r.get("payload_bytes")!=src.get("focus_payload_bytes") or r.get("full_payload_bytes")!=f["full_payload_bytes"] or r.get("payload_bytes",0)>=f["full_payload_bytes"]: errors.append("payload-accounting:"+str(r.get("case_id")))
  if r.get("ocr_exit")!=0: errors.append("ocr-exit:"+str(r.get("case_id")))
  try:
   data=(ROOT/rel).read_bytes()
   if sha(data)!=r.get("input_sha256") or sha(data)!=src.get("focus_png_sha256"): errors.append("input-hash:"+str(r.get("case_id")))
   stdout=base64.b64decode(r.get("ocr_stdout_b64",""),validate=True)
   stderr=base64.b64decode(r.get("ocr_stderr_b64",""),validate=True)
   if sha(stdout)!=r.get("ocr_stdout_sha256") or stdout.decode("utf-8","replace")!=r.get("ocr_text") or sha(stderr)!=r.get("ocr_stderr_sha256") or stderr.decode("utf-8","replace")!=r.get("ocr_stderr"): errors.append("ocr-bytes:"+str(r.get("case_id")))
  except Exception: errors.append("raw-bytes:"+str(r.get("case_id")))
  if f["target_token"] in r.get("ocr_text",""): matches.append(r["case_id"])
 return errors,matches
def mutations(raw):
 def false_exit(x): x["rows"][0]["ocr_exit"]=9
 def wrong_hash(x): x["rows"][0]["input_sha256"]="0"*64
 def wrong_payload(x): x["rows"][0]["payload_bytes"]=-1
 def text_tamper(x): x["rows"][0]["ocr_text"]+="t001101"
 return [("drop-row",lambda x:x["rows"].pop(),"coverage"),("duplicate-id",lambda x:x["rows"].__setitem__(1,copy.deepcopy(x["rows"][0])),"case-identities"),("false-exit",false_exit,"ocr-exit:"),("wrong-input-hash",wrong_hash,"input-hash:"),("wrong-payload",wrong_payload,"payload-accounting:"),("ocr-text-tamper",text_tamper,"ocr-bytes:")]
def main():
 fbytes=(PKG/"FREEZE.json").read_bytes(); f=json.loads(fbytes); freeze_sha=sha(fbytes); raw=json.load(sys.stdin); a04=json.loads((ROOT/f["a04_candidate_path"]).read_text()); design=json.loads((ROOT/f["a04_design_path"]).read_text()); oracle=json.loads((ROOT/f["result_json_path"]).read_text()); submitted=(ROOT/f["submitted_path"]).read_text(); pilot=(PKG/f["pilot_stdout_path"]).read_bytes()
 errors,matches=check(raw,f,a04,design,oracle,submitted,pilot,freeze_sha)
 for rel,h in f["inputs"].items():
  try:
   if sha((ROOT/rel).read_bytes())!=h: errors.append("frozen-input:"+rel)
  except OSError: errors.append("frozen-input-missing:"+rel)
 for rel,h in f["code_sources"].items():
  if sha((PKG/rel).read_bytes())!=h: errors.append("frozen-code:"+rel)
 if sha(pathlib.Path(f["tesseract_path"]).read_bytes())!=f["tesseract_sha256"] or sha(pathlib.Path(f["eng_traineddata_path"]).read_bytes())!=f["eng_traineddata_sha256"]: errors.append("ocr-tool-identity")
 controls=[]; baseline=set(errors)
 for name,mutate,prefix in mutations(raw):
  altered=copy.deepcopy(raw); mutate(altered); changed,_=check(altered,f,a04,design,oracle,submitted,pilot,freeze_sha)
  controls.append({"name":name,"rejected":any(e not in baseline and e.startswith(prefix) for e in changed),"detector_prefix":prefix})
 if not all(c["rejected"] for c in controls): errors.append("mutation-controls")
 disp="PASS_METHOD_SCOPED" if not errors and matches else "FAIL_NO_CROP_TOKEN" if not errors else "STOP_AUDIT"
 result={"schema":"a09-audit-v1","errors":errors,"crop_count":len(raw.get("rows",[])),"exact_token_crop_ids":matches,"mutation_controls":controls,"disposition":disp}
 print(json.dumps(result,sort_keys=True,separators=(",",":"))); return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())
