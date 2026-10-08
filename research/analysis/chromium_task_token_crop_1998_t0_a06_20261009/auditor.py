#!/usr/bin/env python3
"""Independent stdlib raw-output custody and decision audit."""
import hashlib, json, pathlib, re, sys
ROOT=pathlib.Path(__file__).resolve().parents[3]; PKG=pathlib.Path(__file__).resolve().parent
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
    fb=(PKG/"FREEZE.json").read_bytes(); f=json.loads(fb); raw=json.load(sys.stdin); errors=[]
    for rel, expected in f["inputs"].items():
        try:
            if sha((ROOT/rel).read_bytes()) != expected: errors.append("input:"+rel)
        except OSError: errors.append("input-missing:"+rel)
    for rel, expected in f["code_sources"].items():
        if sha((PKG/rel).read_bytes()) != expected: errors.append("code:"+rel)
    for path,key in ((f["tesseract_path"],"tesseract_sha256"),(f["eng_traineddata_path"],"eng_traineddata_sha256")):
        if sha(pathlib.Path(path).read_bytes()) != f[key]: errors.append("tool:"+key)
    rows=raw.get("rows",[]); ids=[r.get("case_id") for r in rows]
    a04=json.loads((ROOT/f["a04_candidate_path"]).read_text()); expected={r["case_id"]:r for r in a04["rows"] if r["frame_id"]==f["frame_id"] and r["selected_kind"]=="FOCUSED_REGION"]
    if raw.get("schema")!="a06-ocr-output-v1" or raw.get("case_count")!=20 or len(rows)!=20: errors.append("coverage")
    if len(set(ids))!=20 or set(ids)!=set(expected): errors.append("case-identities")
    if raw.get("freeze_sha256")!=sha(fb): errors.append("freeze-identity")
    found=[]; saves=[]
    for r in rows:
        src=expected.get(r.get("case_id"),{}); rel=f["a04_package"]+"/"+src.get("focus_png_path","")
        if r.get("png_path")!=rel or r.get("bounds")!=src.get("request",{}).get("bounds"): errors.append("crop-identity:"+str(r.get("case_id")))
        if r.get("payload_bytes")!=src.get("focus_payload_bytes") or r.get("full_payload_bytes")!=f["full_payload_bytes"] or r.get("payload_bytes",0)>=f["full_payload_bytes"]: errors.append("payload-accounting:"+str(r.get("case_id")))
        if r.get("ocr_exit")!=0: errors.append("ocr-exit:"+str(r.get("case_id")))
        try:
            if sha((ROOT/rel).read_bytes())!=r.get("input_sha256"): errors.append("png-hash:"+str(r.get("case_id")))
        except OSError: errors.append("png-missing:"+str(r.get("case_id")))
        if isinstance(r.get("ocr_text"),str) and re.search(re.escape(f["marker"]),r["ocr_text"]): found.append(r["case_id"])
        if r.get("payload_bytes",0)<f["full_payload_bytes"]: saves.append(r["case_id"])
    mutations=[]
    for name,fn in (("drop-row",lambda x:x["rows"].pop()),("duplicate-id",lambda x:x["rows"].__setitem__(1,dict(x["rows"][0]))),("wrong-freeze",lambda x:x.__setitem__("freeze_sha256","0"*64)),("false-exit",lambda x:x["rows"][0].__setitem__("ocr_exit",9)),("wrong-input",lambda x:x["rows"][0].__setitem__("input_sha256","0"*64)),("wrong-payload",lambda x:x["rows"][0].__setitem__("payload_bytes",-1))):
        x=json.loads(json.dumps(raw)); fn(x); rejected=(len(x.get("rows",[]))!=20 or len({r.get("case_id") for r in x.get("rows",[])})!=20 or x.get("freeze_sha256")!=sha(fb) or any(r.get("ocr_exit")!=0 for r in x.get("rows",[])) or any(r.get("input_sha256")=="0"*64 for r in x.get("rows",[])) or any(r.get("payload_bytes")==-1 for r in x.get("rows",[]))); mutations.append({"name":name,"rejected":rejected})
    if not all(m["rejected"] for m in mutations): errors.append("mutations")
    result={"schema":"a06-audit-v1","errors":errors,"crop_count":len(rows),"strict_saving_crops":saves,"marker_crop_ids":found,"mutations":mutations,"disposition":"PASS_METHOD_SCOPED" if not errors and found else "FAIL_NO_CROP_MARKER" if not errors else "STOP_AUDIT"}
    print(json.dumps(result,sort_keys=True,separators=(",",":"))); return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())
