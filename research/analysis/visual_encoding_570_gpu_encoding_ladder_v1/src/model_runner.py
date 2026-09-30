from __future__ import annotations
import argparse, base64, hashlib, json, time, urllib.request
from pathlib import Path

MODEL="qwen2.5vl:3b"; DIGEST="fb90415cde1ef08aa669ae74b082d49b158729b6db1ab183c941417d507e71a1"
SCHEMA={"type":"object","properties":{"present":{"type":"boolean"},"box":{"type":["array","null"],"items":{"type":"integer"},"minItems":4,"maxItems":4}},"required":["present","box"],"additionalProperties":False}
def sha(b): return hashlib.sha256(b).hexdigest()
def get(url):
    with urllib.request.urlopen(url,timeout=15) as r: return json.loads(r.read())
def post(url,obj):
    data=json.dumps(obj,separators=(",",":")).encode(); req=urllib.request.Request(url,data=data,headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=300) as r: return json.loads(r.read())
def main():
    p=argparse.ArgumentParser(); p.add_argument("--mode",choices=["identity","formal"],required=True); p.add_argument("--url",default="http://ollama:11434"); p.add_argument("--data",type=Path,default=Path("/data")); p.add_argument("--out",type=Path,default=Path("/out")); a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    if a.mode=="identity":
        tags=get(a.url+"/api/tags"); matches=[x for x in tags.get("models",[]) if x.get("name")==MODEL]
        out={"models":matches,"expected_digest":DIGEST}; (a.out/"model_identity.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
        if len(matches)!=1 or matches[0].get("digest")!=DIGEST: raise SystemExit("exact cached model digest unavailable")
        print(json.dumps(out)); return
    pre=json.loads((a.data/"PREFORMAL.json").read_text(encoding="utf-8")); (a.out/"formal").mkdir(exist_ok=True)
    for case in pre["formal_cases"]:
        path=a.data/case["image_path"]; img=path.read_bytes(); request={"model":MODEL,"messages":[{"role":"user","content":pre["prompt"],"images":[base64.b64encode(img).decode("ascii")]}],"format":SCHEMA,"stream":False,"keep_alive":"5m","options":{"temperature":0,"seed":case["seed"],"num_predict":128}}
        start=time.time_ns(); response=None; error=None
        try: response=post(a.url+"/api/chat",request)
        except Exception as e: error=f"{type(e).__name__}: {e}"
        end=time.time_ns(); rec={"schema":"visual-encoding-570-r5-raw-call-v1","case_id":case["case_id"],"source_case_id":case["source_case_id"],"arm":case["arm"],"seed":case["seed"],"model":MODEL,"expected_digest":DIGEST,"request":request,"request_sha256":sha(json.dumps(request,sort_keys=True,separators=(",",":")).encode()),"image_sha256":case["image_sha256"],"source_sha256":case["source_sha256"],"mapping":case["mapping"],"started_utc_ns":start,"ended_utc_ns":end,"response":response,"error":error}
        (a.out/"formal"/(case["case_id"]+".json")).write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        if error: raise SystemExit(f"first failed request retained; no retry: {case['case_id']}: {error}")
    print(json.dumps({"formal_requests":len(pre["formal_cases"]),"result":"complete"}))
if __name__=="__main__": main()
