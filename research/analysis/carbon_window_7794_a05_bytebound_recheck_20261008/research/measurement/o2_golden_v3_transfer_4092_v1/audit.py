"""Independent raw audit for Issue #4103.

Does not import run.py, transfer.py, VectorEncoder, or ContiguousEncoder.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, os, statistics, sys
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("AGENT_INTERFACE_ROOT", HERE.parents[2]))
sys.path.insert(0, str(ROOT / "research" / "observation_tiles"))
import tile_transport as reference
GOLDEN = ROOT / "runtime/results/golden-desktop-app-server-v3-live-01/arms/persistent/runtime"
MED = statistics.median


def req(x, msg):
    if not x: raise ValueError(msg)

def integer(x): return type(x) is int and x >= 0

def sha(data): return hashlib.sha256(data).hexdigest()
def blob(data): return hashlib.sha1(f"blob {len(data)}\0".encode()+data).hexdigest()

def pixels(path):
    raw=path.read_bytes()
    with Image.open(path) as im:
        rgb=im.convert("RGB"); w,h=rgb.size; p=rgb.tobytes()
    return raw,w,h,p

def load(root,schedule):
    data={}
    for spec in schedule["pairs"]:
        p=root/spec["id"]/"raw.json"; req(p.exists(),"missing raw")
        data[spec["id"]]=json.loads(p.read_text())
    return data

def validate(root,schedule,data,source_check=True):
    req(list(data)==[p["id"] for p in schedule["pairs"]],"pair order/denominator")
    metrics=[]
    for index,spec in enumerate(schedule["pairs"]):
        d=data[spec["id"]]; req(d["id"]==spec["id"] and d["index"]==index,"pair identity")
        rb,w,h,bp=pixels(GOLDEN/spec["before"]); ra,w2,h2,ap=pixels(GOLDEN/spec["after"])
        req(blob(rb)==spec["before_blob"] and blob(ra)==spec["after_blob"],"image git identity")
        req((w,h)==(w2,h2)==(d["width"],d["height"]),"geometry")
        req(sha(rb)==d["before_png_sha256"] and sha(ra)==d["after_png_sha256"],"png hash")
        req(sha(bp)==d["before_pixel_sha256"] and sha(ap)==d["after_pixel_sha256"],"pixel hash")
        stream="golden-"+spec["id"]
        dec=reference.Decoder(stream)
        wi=(root/spec["id"]/'canonical-initial.wire').read_bytes(); wu=(root/spec["id"]/'canonical-update.wire').read_bytes()
        f1=dec.accept(wi); f2=dec.accept(wu)
        req((f1.width,f1.height,f1.mode,f1.pixels)==(w,h,"RGB",bp),"decoded before")
        req((f2.width,f2.height,f2.mode,f2.pixels)==(w,h,"RGB",ap),"decoded after")
        req(sha(wi)==d["canonical_initial_sha256"] and sha(wu)==d["canonical_update_sha256"],"canonical wire hash")
        req(len(wu)==d["canonical_wire_bytes"],"wire bytes")
        for arm in ["vector","contiguous"]:
            one=(root/spec["id"]/(arm+'-update.wire')).read_bytes()
            req(one==wu,"retained arm wire")
        samples=d["samples"]
        req(len(samples)==schedule["warmups"]+schedule["timed"],"sample denominator")
        ratios=[]
        for ordinal,row in enumerate(samples):
            req(row["ordinal"]==ordinal and type(row["ordinal"]) is int,"ordinal")
            req(row["phase"]==("warmup" if ordinal<schedule["warmups"] else "timed"),"phase")
            expected=["vector","contiguous"] if (ordinal+index)%2==0 else ["contiguous","vector"]
            req(row["order"]==expected and set(row["arms"])=={"vector","contiguous"},"order")
            for arm in expected:
                x=row["arms"][arm]
                req(integer(x["wall_ns"]) and x["wall_ns"]>0 and integer(x["cpu_ns"]),"timing")
                req(x["initial_sha256"]==d["canonical_initial_sha256"] and x["wire_sha256"]==d["canonical_update_sha256"],"sample wire")
                req(x["wire_bytes"]==d["canonical_wire_bytes"] and type(x["wire_bytes"]) is int,"sample bytes")
                req(type(x["changed_tiles"]) is int and x["changed_tiles"]>=0,"changed tiles")
                req(x["kind"]==d["canonical_kind"],"kind")
            if row["phase"]=="timed": ratios.append(row["arms"]["contiguous"]["wall_ns"]/row["arms"]["vector"]["wall_ns"])
        rm=MED(ratios)
        metrics.append({"id":spec["id"],"ratio_median":rm,"ratio_min":min(ratios),"ratio_max":max(ratios),
                        "vector_median_ns":MED(r["arms"]["vector"]["wall_ns"] for r in samples if r["phase"]=="timed"),
                        "contiguous_median_ns":MED(r["arms"]["contiguous"]["wall_ns"] for r in samples if r["phase"]=="timed"),
                        "wire_bytes":d["canonical_wire_bytes"],"kind":d["canonical_kind"],"changed_tiles":d["canonical_changed_tiles"]})
    pair_gate=all(m["ratio_median"]<=schedule["pair_ratio_max"] for m in metrics)
    aggregate=MED(m["ratio_median"] for m in metrics)
    strong=sum(m["ratio_median"]<=schedule["strong_pair_ratio_max"] for m in metrics)
    benefit=pair_gate and aggregate<=schedule["aggregate_ratio_max"] and strong>=schedule["strong_pair_min_count"]
    return {"integrity":"PASS_RAW_GOLDEN_TRANSFER_AUDIT","errors":[],"pair_count":len(metrics),
            "timed_pairs":len(metrics)*schedule["timed"],"pair_gate":pair_gate,"aggregate_ratio_median":aggregate,
            "strong_pair_count":strong,"benefit_gate":benefit,"metrics":metrics,
            "decision":"PASS_GOLDEN_V3_CONTIGUOUS_TRANSFER_SCOPED" if benefit else "HOLD_GOLDEN_TRANSFER_BENEFIT_NOT_ESTABLISHED"}

def controls(root,schedule,data):
    names=["missing_pair","duplicate_sample","bool_duration","wrong_wire","wrong_image_blob","wrong_order","missing_arm","wrong_pixel_hash","wrong_ordinal"]
    out={}; key=list(data)[0]
    for name in names:
        d=copy.deepcopy(data); row=d[key]["samples"][6]
        if name=="missing_pair": d.pop(list(d)[-1])
        elif name=="duplicate_sample": d[key]["samples"][7]=copy.deepcopy(row)
        elif name=="bool_duration": row["arms"]["vector"]["wall_ns"]=True
        elif name=="wrong_wire": row["arms"]["contiguous"]["wire_sha256"]="0"*64
        elif name=="wrong_image_blob":
            # schedule is copied for this mutation below
            pass
        elif name=="wrong_order": row["order"]=list(reversed(row["order"]))
        elif name=="missing_arm": row["arms"].pop("vector")
        elif name=="wrong_pixel_hash": d[key]["after_pixel_sha256"]="0"*64
        elif name=="wrong_ordinal": row["ordinal"]+=1
        sc=copy.deepcopy(schedule)
        if name=="wrong_image_blob": sc["pairs"][0]["after_blob"]="0"*40
        try: validate(root,sc,d)
        except (ValueError,KeyError,IndexError,TypeError) as e: out[name]={"rejected":True,"reason":str(e)}
        else: out[name]={"rejected":False}
    req(all(v["rejected"] for v in out.values()),"accepted corruption")
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=Path,required=True); ap.add_argument("--controls",action="store_true"); a=ap.parse_args()
    schedule=json.loads((HERE/"schedule.json").read_text()); freeze=json.loads((HERE/"FREEZE.json").read_text())
    for p,h in freeze["source_sha256"].items(): req(sha((ROOT/p).read_bytes())==h,"source freeze "+p)
    for p,h in freeze["source_git_blobs"].items(): req(blob((ROOT/p).read_bytes())==h,"source git blob "+p)
    data=load(a.root,schedule); result=validate(a.root,schedule,data)
    end=json.loads((a.root/"END.json").read_text()); req(end["status"]=="COMPLETE" and end["pair_count"]==8 and end["timed_pairs"]==248,"end receipt")
    start=json.loads((a.root/"START.json").read_text()); req(start["freeze_sha256"]==sha((HERE/"FREEZE.json").read_bytes()),"freeze receipt")
    req(start["numpy"]==freeze["expected_formal_env"]["numpy"] and start["pillow"]==freeze["expected_formal_env"]["pillow"],"formal dependency identity")
    req(int((a.root/"FORMAL_CONTAINER_EXIT.host").read_text().strip())==0,"formal container exit")
    if a.controls: result["corruption_controls"]=controls(a.root,schedule,data)
    print(json.dumps(result,sort_keys=True,indent=2))
if __name__=="__main__": main()
