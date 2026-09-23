import hashlib, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"result.json"
ALLOWED={"pixel_difference","layout_change","focus_change","inferred"}
def validate(c):
    if not isinstance(c,dict): return "UNKNOWN"
    if not isinstance(c.get("frame"),str) or not c["frame"]: return "UNKNOWN"
    if not isinstance(c.get("source"),str) or c["source"] not in ("observed","inferred"): return "UNKNOWN"
    conf=c.get("confidence")
    if isinstance(conf,bool) or not isinstance(conf,(int,float)) or not math.isfinite(conf) or not 0<=conf<=1: return "UNKNOWN"
    if c.get("change_type") not in ALLOWED: return "UNKNOWN"
    r=c.get("region")
    if not isinstance(r,dict) or any(type(r.get(k)) is not int for k in ("x","y","w","h")) or r["w"]<=0 or r["h"]<=0 or r["x"]<0 or r["y"]<0: return "UNKNOWN"
    if c.get("authority") is not False: return "UNKNOWN"
    return "ADMIT"
def main():
    base={"frame":"f1","source":"observed","confidence":0.8,"change_type":"pixel_difference","region":{"x":1,"y":2,"w":10,"h":8},"authority":False}
    cases=[(base,"ADMIT"),({**base,"source":"inferred","change_type":"inferred"},"ADMIT"),
      ({k:v for k,v in base.items() if k!="frame"},"UNKNOWN"),({**base,"frame":None},"UNKNOWN"),({**base,"source":3},"UNKNOWN"),
      ({**base,"confidence":True},"UNKNOWN"),({**base,"confidence":float("nan")},"UNKNOWN"),({**base,"confidence":1.2},"UNKNOWN"),
      ({**base,"change_type":"other"},"UNKNOWN"),({**base,"region":{"x":1,"y":2,"w":0,"h":8}},"UNKNOWN"),({**base,"authority":True},"UNKNOWN")]
    rows=[{"i":i,"expected":e,"actual":validate(c),"ok":validate(c)==e} for i,(c,e) in enumerate(cases)]
    assert len(rows)==11 and all(r["ok"] for r in rows)
    raw=json.dumps(rows,sort_keys=True,separators=(",",":"),allow_nan=True).encode()
    result={"decision":"PASS_ATTENTION_PROVENANCE_VALUE_REPAIR_SCOPED","cases":11,"admitted":sum(r["actual"]=="ADMIT" for r in rows),"unknown":sum(r["actual"]=="UNKNOWN" for r in rows),"mismatches":0,"authority_true":0,"rows_sha256":hashlib.sha256(raw).hexdigest(),"model_gui_network_runtime_task_input":0}
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
