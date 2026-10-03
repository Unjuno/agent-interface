"""Independent stdlib-only saved telemetry oracle; imports no candidate/baseline."""
import argparse
import base64
import hashlib
import json
import struct
from pathlib import Path

def parse(raw):
    def unique(pairs):
        d = {}
        for k,v in pairs:
            if k in d: raise ValueError("duplicate JSON field")
            d[k] = v
        return d
    def bad(v): raise ValueError("nonfinite JSON")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=bad)

def join(a,b,message):
    if json.dumps(a,sort_keys=True,allow_nan=False) != json.dumps(b,sort_keys=True,allow_nan=False):
        raise ValueError(message)

def require(ok,message):
    if not ok: raise ValueError(message)

def integer(v):
    require(type(v) is int and v >= 0, "nonnegative plain integer")
    return v

def cpu(raw):
    d = {}
    for line in raw.splitlines():
        s = line.split()
        require(len(s)==2 and s[0] not in d and s[1].isdigit(), "CPU grammar")
        d[s[0]] = int(s[1])
    return d

def delta(a,b):
    integer(a); integer(b)
    require(b>=a, "counter regression")
    return b-a

def snap(v):
    t = [integer(v[k]) for k in ("begin_ns","cpu_read_begin_ns","cpu_read_end_ns","end_ns")]
    require(t==sorted(t), "snapshot chronology")
    join(v["cpu_stat"], cpu(v["cpu_stat_raw"]), "CPU raw join")
    for k in ("usage_usec","nr_periods","nr_throttled","throttled_usec"): integer(v["cpu_stat"][k])
    for k in ("process_cpu_ns","thread_cpu_ns","voluntary","involuntary"): integer(v[k])
    for k in ("cpu_stat_local","schedstat","schedstats_enabled"):
        x = v[k]
        require(type(x["available"]) is bool, "availability type")
        require((type(x["raw"]) is str and x["error"] is None) if x["available"] else
                (x["raw"] is None and type(x["error"]) is dict), "optional custody")

def frame_metrics(f,due):
    integer(due); integer(f["index"]); join(f["due_ns"],due,"deadline")
    a,b,w = f["pre"],f["post"],f["wait"]
    snap(a); snap(b)
    chain = [a["end_ns"],integer(w["begin_ns"]),integer(w["return_ns"]),b["begin_ns"],b["end_ns"],
             integer(f["start_ns"]),integer(f["native_return_ns"]),integer(f["extracted_ns"])]
    require(chain==sorted(chain),"native chronology")
    previous = w["begin_ns"]
    for s in w["sleeps"]:
        start,end,requested = [integer(s[k]) for k in ("start_ns","return_ns","requested_ns")]
        require(previous<=start<=end<=w["return_ns"],"sleep chronology")
        require(requested==due-start-15_000_000 and requested>0,"prospective sleep")
        previous = end
    if w["spin_enter_ns"] is not None:
        require(previous<=integer(w["spin_enter_ns"])<=w["return_ns"],"spin chronology")
    require(w["return_ns"]>=due,"early pacing")
    try: raw = base64.b64decode(f["pixels_b64"],validate=True)
    except Exception as e: raise ValueError("pixel encoding") from e
    require(len(raw)==4096 and hashlib.sha256(raw).hexdigest()==f["pixel_sha256"],"pixel custody")
    require(all(x==0 for x in struct.unpack("<1024I",raw)) and f["decoded"] is None,"dark pixels")
    counters = {k:delta(a["cpu_stat"][k],b["cpu_stat"][k]) for k in
                ("usage_usec","nr_periods","nr_throttled","throttled_usec")}
    local,runqueue = None,None
    if all(s["cpu_stat_local"]["available"] for s in (a,b)):
        x,y = [cpu(s["cpu_stat_local"]["raw"]) for s in (a,b)]
        require(x.keys()==y.keys(),"local CPU schema")
        local = {k:delta(x[k],y[k]) for k in x}
    if all(s["schedstats_enabled"]["available"] and s["schedstats_enabled"]["raw"].strip()=="1"
           and s["schedstat"]["available"] for s in (a,b)):
        x,y = [s["schedstat"]["raw"].split() for s in (a,b)]
        require(len(x)==len(y)==3 and all(i.isdigit() for i in x+y),"schedstat grammar")
        runqueue = delta(int(x[1]),int(y[1]))
    r = {"wait_lateness_ns":w["return_ns"]-due,"capture_lateness_ns":f["start_ns"]-due,
         "post_wait_overhead_ns":f["start_ns"]-w["return_ns"],
         "wait_begin_lateness_ns":max(0,w["begin_ns"]-due),
         "native_duration_ns":f["native_return_ns"]-f["start_ns"],
         "extraction_duration_ns":f["extracted_ns"]-f["native_return_ns"],
         "leaf_nr_throttled_delta":counters["nr_throttled"],
         "leaf_throttled_usec_delta":counters["throttled_usec"],
         "leaf_cpu_usage_usec_delta":counters["usage_usec"],"leaf_nr_periods_delta":counters["nr_periods"],
         "cpu_stat_local_delta":local,"runqueue_wait_ns_delta":runqueue,
         "coarse_wake_past_deadline":any(s["return_ns"]>due for s in w["sleeps"])}
    for k in ("process_cpu_ns","thread_cpu_ns","voluntary","involuntary"):
        r[k+"_delta"] = delta(a[k],b[k])
    return r

def read(p): return parse(Path(p).read_text())
def stream(p): return [parse(x) for x in Path(p).read_text().splitlines()]

def check_plan(plan):
    conditions = [(1,"fixed",[0]*4),(1,"irregular",[1,7,3,9]),(2,"fixed",[0]*4),(2,"irregular",[1,7,3,9])]
    expected = []
    for row in range(4):
        for pos in range(4):
            c,s,o = conditions[(row+pos)%4]
            expected.append({"id":f"d{len(expected):03}","cpu":c,"schedule":s,"offsets":o,"kind":"dark"})
    join(plan["cells"],expected,"complete independently reconstructed contrast")
    for k,v in {"samples_per_cell":8,"final_spin_ns":15_000_000,"epoch_lead_ns":200_000_000,"threshold_ns":10_000_000}.items():
        join(plan[k],v,"prospective header")
    join(plan["allocation"],"PHASE-DEADLINE-6067-D01-20261003-3CBF","allocation")
    return expected

def inspect_runtime(launch,plan,case,command):
    join(launch["command"],command,"frozen command")
    for k in ("exit_code","inspect_exit"): join(launch[k],0,"terminal launch")
    require(integer(launch["started_ns"])<integer(launch["finished_ns"]),"host chronology")
    i = parse(launch["inspect_stdout"])
    join(i["Image"],plan["image_id"],"immutable image")
    join(i["Config"]["User"],"501:501","unprivileged user")
    join(i["RestartCount"],0,"no restart")
    for k,v in {"Running":False,"OOMKilled":False,"Restarting":False,"ExitCode":0}.items(): join(i["State"][k],v,"terminal state")
    h = i["HostConfig"]
    for k,v in {"NanoCpus":case["cpu"]*1_000_000_000,"Memory":536870912,"MemorySwap":536870912,
                "PidsLimit":64,"ReadonlyRootfs":True,"NetworkMode":"none"}.items(): join(h[k],v,"resources")
    require("ALL" in h["CapDrop"] and "no-new-privileges" in h["SecurityOpt"],"capabilities")
    mounts = {m["Destination"]:m for m in i["Mounts"]}
    for destination,argindex,rw in (("/src",command.index("--mount")+1,False),("/out",command.index("--mount")+3,True)):
        join(mounts[destination]["RW"],rw,"mount permissions")
        join(mounts[destination]["Source"],command[argindex].split("src=")[1].split(",")[0],"mount path")

def cell_metrics(root,case,plan,command,mode="diagnostic"):
    root = Path(root); record = root/"record"
    inspect_runtime(read(root/"launch.json"),plan,case,command)
    join(read(root/"copy.json")["exit"],0,"retention")
    c = read(record/"cell.json")
    for k,v in {"status":"COMPLETE_DIAGNOSTIC","mode":mode,"allocation":plan["allocation"],"case":case,
                "input_events":0,"model_calls":0,"scientific_t1_cells":0}.items(): join(c[k],v,"native contract")
    join(read(record/"spec.json"),case,"actual spec")
    for k,v in {"cpu.max":f'{case["cpu"]*100000} 100000',"memory.max":"536870912","memory.swap.max":"0","pids.max":"64"}.items():
        join(c["cgroups"][k],v,"actual cgroups")
    hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in record.iterdir() if p.is_file() and p.name!="cell.json"}
    join(c["files_sha256"],hashes,"complete raw file set")
    life = c["lifecycle"]
    pids = [integer(life[n+"_pid"]) for n in ("xvfb","fixture","observer")]
    require(len(set(pids))==3 and all(p>0 for p in pids),"separate child PIDs")
    for n in ("xvfb","fixture","observer"): join(life[n+"_exit"],0,"all children terminal")
    source,capture = read(record/"source.json"),read(record/"capture.json")
    fready,oready,epoch = read(record/"fixture-ready.json"),read(record/"observer-ready.json"),read(record/"epoch.json")
    join(source["pid"],life["fixture_pid"],"source PID"); join(capture["pid"],life["observer_pid"],"observer PID")
    join(fready,{"pid":source["pid"],"window":source["window"]},"source readiness")
    join(oready,{"pid":capture["pid"],"initial_keymap":capture["initial_keymap"]},"observer readiness")
    integer(source["window"]); join(capture["window"],source["window"],"window")
    e = integer(epoch["epoch_ns"])
    join(source["epoch_ns"],e,"source epoch"); join(capture["epoch_ns"],e,"capture epoch")
    require(integer(capture["epoch_read_ns"])<=e,"future epoch readiness")
    join(source["events"],[],"dark events"); join(stream(record/"source.jsonl"),[],"dark journal")
    join(source["final_pixels"],[0]*1024,"source neutral pixels")
    join(source["final_keymap"],"00"*32,"source neutral keys")
    for k in ("initial_keymap","final_keymap"): join(capture[k],"00"*32,"capture neutral keys")
    frames,waits = stream(record/"frames.jsonl"),stream(record/"waits.jsonl")
    join(capture["frames"],frames,"frame stream")
    require(len(frames)==len(waits)==8,"eight actual acquisitions")
    metrics = []
    for index,f in enumerate(frames):
        join(f["index"],index,"frame order")
        due = e+(index*120+case["offsets"][index%4]*10+5)*1_000_000
        join(waits[index],{k:f[k] for k in ("index","due_ns","pre","wait","post")},"flushed wait trace")
        r = frame_metrics(f,due)
        require(f["extracted_ns"]<=e+1_050_000_000,"source window")
        metrics.append(dict(r,id=case["id"],index=index,cpu=case["cpu"],schedule=case["schedule"]))
    return metrics

def audit(raw,plan,freeze):
    raw = Path(raw); expected = check_plan(plan)
    summary = read(raw/"raw.json")
    for k,v in {"allocation":plan["allocation"],"mode":"diagnostic","status":"COMPLETE_DIAGNOSTIC",
                "started_cells":[c["id"] for c in expected],"completed_cells":[c["id"] for c in expected],
                "input_events":0,"model_calls":0,"scientific_t1_cells":0}.items(): join(summary[k],v,"complete run")
    frames = []
    for c in expected: frames.extend(cell_metrics(raw/c["id"],c,plan,freeze["commands"][c["id"]]))
    late = [f for f in frames if f["wait_lateness_ns"]>10_000_000]
    contrary = [f for f in late if f["leaf_nr_throttled_delta"]==0]
    status = "COUNTEREXAMPLE_LEAF_THROTTLE_NECESSITY" if contrary else "ASSOCIATION_ONLY" if late else "HOLD_NOT_REPRODUCED"
    arms = []
    for quota in (1,2):
        for schedule in ("fixed","irregular"):
            g = [f for f in frames if f["cpu"]==quota and f["schedule"]==schedule]
            arms.append({"cpu":quota,"schedule":schedule,"frames":len(g),
                "late_waits":sum(f["wait_lateness_ns"]>10_000_000 for f in g),
                "late_captures":sum(f["capture_lateness_ns"]>10_000_000 for f in g),
                "max_wait_lateness_ns":max(f["wait_lateness_ns"] for f in g),
                "max_capture_lateness_ns":max(f["capture_lateness_ns"] for f in g),
                "leaf_throttle_events_delta":sum(f["leaf_nr_throttled_delta"] for f in g)})
    return {"status":status,"valid_cells":16,"native_frames":len(frames),"late_waits":len(late),
            "leaf_unthrottled_late_waits":len(contrary),"arms":arms,"frames":frames,
            "scientific_t1_cells":0,"input_events":0,"model_calls":0,
            "scope":"Instrumented static dark diagnosis only; not A01 replay, T1 benefit, live effect or causality.",
            "limitations":"Leaf counters do not exclude ancestor/host/guest scheduling; unavailable schedstats are not zero."}

def main():
    ap = argparse.ArgumentParser()
    for k in ("raw","plan","freeze","out"): ap.add_argument("--"+k,type=Path,required=True)
    a = ap.parse_args(); frozen = read(a.freeze); here = Path(__file__).resolve().parent
    for name,digest in frozen["source_sha256"].items():
        require(hashlib.sha256((here/name).read_bytes()).hexdigest()==digest,"source freeze")
    result = audit(a.raw,read(a.plan),frozen)
    with a.out.open("x") as f:
        json.dump(result,f,sort_keys=True,indent=2); f.write("\n")
if __name__=="__main__": main()
