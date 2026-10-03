"""Producer fail-fast validity gates; imports neither auditor nor native bridge."""
import base64
import hashlib
import json
import struct
from pathlib import Path

def require(ok,message):
    if not ok: raise ValueError(message)
def plain(value):
    require(type(value) is int and value>=0,"nonnegative integer")
    return value
def typed(a,b):
    require(json.dumps(a,sort_keys=True,allow_nan=False)==json.dumps(b,sort_keys=True,allow_nan=False),"typed producer join")
def read(p):
    def pairs(items):
        d={}
        for k,v in items:
            require(k not in d,"duplicate field"); d[k]=v
        return d
    def bad(v): raise ValueError("nonfinite")
    return json.loads(Path(p).read_text(),object_pairs_hook=pairs,parse_constant=bad)
def preflight(plan,freeze,source,prefix,command):
    typed(set(freeze["commands"])==set(c["id"] for c in plan["cells"]),True)
    for c in plan["cells"]:
        typed(command(plan,c,source,prefix+"-"+c["id"],"diagnostic-only"),freeze["commands"][c["id"]])
def counter(raw):
    d={}
    for line in raw.splitlines():
        p=line.split()
        require(len(p)==2 and p[0] not in d and p[1].isdigit(),"counter grammar")
        d[p[0]]=int(p[1])
    return d
def frame_valid(f):
    for s in (f["pre"],f["post"]):
        typed(s["cpu_stat"],counter(s["cpu_stat_raw"]))
        for k in ("usage_usec","nr_periods","nr_throttled","throttled_usec"): plain(s["cpu_stat"][k])
        ts=[plain(s[k]) for k in ("begin_ns","cpu_read_begin_ns","cpu_read_end_ns","end_ns")]
        require(ts==sorted(ts),"snapshot order")
        for k in ("process_cpu_ns","thread_cpu_ns","voluntary","involuntary"): plain(s[k])
        for k in ("schedstat","schedstats_enabled","cpu_stat_local"):
            v=s[k]; require(type(v["available"]) is bool,"availability")
            if v["available"]:
                require(type(v["raw"]) is str and v["error"] is None,"present optional")
                if k=="schedstat":
                    t=v["raw"].split(); require(len(t)==3 and all(x.isdigit() for x in t),"schedstat grammar")
                elif k=="schedstats_enabled": require(v["raw"].strip() in ("0","1"),"enabled grammar")
                else: counter(v["raw"])
            else: require(v["raw"] is None and type(v["error"]) is dict,"absent optional")
    for k in ("usage_usec","nr_periods","nr_throttled","throttled_usec"):
        require(f["post"]["cpu_stat"][k]>=f["pre"]["cpu_stat"][k],"counter regression")
    for k in ("process_cpu_ns","thread_cpu_ns","voluntary","involuntary"):
        require(f["post"][k]>=f["pre"][k],"process counter regression")
    w=f["wait"]; due=plain(f["due_ns"])
    chain=[f["pre"]["end_ns"],plain(w["begin_ns"]),plain(w["return_ns"]),f["post"]["begin_ns"],
           f["post"]["end_ns"],plain(f["start_ns"]),plain(f["native_return_ns"]),plain(f["extracted_ns"])]
    require(chain==sorted(chain),"native chronology")
    now=w["begin_ns"]
    for s in w["sleeps"]:
        typed(s["start_ns"],now)
        require(plain(s["requested_ns"])==due-now-15_000_000 and s["requested_ns"]>0,"sleep request")
        require(now<=plain(s["return_ns"])<=w["return_ns"],"sleep return")
        now=s["return_ns"]
    if w["spin_enter_ns"] is None:
        require(now>=due and now==w["return_ns"],"complete wait trace")
    else:
        typed(w["spin_enter_ns"],now)
        require(0<due-now<=15_000_000 and w["return_ns"]>=due,"spin trace")
    pixels=base64.b64decode(f["pixels_b64"],validate=True)
    require(len(pixels)==4096 and hashlib.sha256(pixels).hexdigest()==f["pixel_sha256"],"raw pixels")
    require(all(v==0 for v in struct.unpack("<1024I",pixels)) and f["decoded"] is None,"dark validity")

def check_cell(root,case,plan):
    root=Path(root); record=root/"record"; launch=read(root/"launch.json")
    typed(launch["exit_code"],0); typed(launch["inspect_exit"],0); typed(read(root/"copy.json")["exit"],0)
    i=json.loads(launch["inspect_stdout"])
    typed(i["Image"],plan["image_id"]); typed(i["RestartCount"],0)
    for k,v in {"Running":False,"OOMKilled":False,"Restarting":False,"ExitCode":0}.items(): typed(i["State"][k],v)
    for k,v in {"NanoCpus":case["cpu"]*1_000_000_000,"Memory":536870912,"MemorySwap":536870912,
                "PidsLimit":64,"ReadonlyRootfs":True,"NetworkMode":"none"}.items(): typed(i["HostConfig"][k],v)
    typed(i["Config"]["User"],"501:501")
    require("ALL" in i["HostConfig"]["CapDrop"] and "no-new-privileges" in i["HostConfig"]["SecurityOpt"],"capabilities")
    m={x["Destination"]:x for x in i["Mounts"]}
    typed(m["/src"]["RW"],False); typed(m["/out"]["RW"],True)
    c=read(record/"cell.json"); typed(c["status"],"COMPLETE_DIAGNOSTIC"); typed(c["case"],case)
    typed(c["allocation"],plan["allocation"])
    for k in ("input_events","model_calls","scientific_t1_cells"): typed(c[k],0)
    typed(read(record/"spec.json"),case)
    for k,v in {"cpu.max":f'{case["cpu"]*100000} 100000',"memory.max":"536870912","memory.swap.max":"0","pids.max":"64"}.items(): typed(c["cgroups"][k],v)
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in record.iterdir() if p.is_file() and p.name!="cell.json"}
    typed(c["files_sha256"],hashes)
    life=c["lifecycle"]; pids=[plain(life[n+"_pid"]) for n in ("xvfb","fixture","observer")]
    require(len(set(pids))==3 and min(pids)>0,"separate PIDs")
    for n in ("xvfb","fixture","observer"): typed(life[n+"_exit"],0)
    source,capture=read(record/"source.json"),read(record/"capture.json")
    e=plain(read(record/"epoch.json")["epoch_ns"])
    typed(source["pid"],life["fixture_pid"]); typed(capture["pid"],life["observer_pid"])
    typed(source["window"],capture["window"]); plain(source["window"])
    typed(source["epoch_ns"],e); typed(capture["epoch_ns"],e)
    require(plain(capture["epoch_read_ns"])<=e,"future epoch")
    typed(source["events"],[]); require((record/"source.jsonl").read_bytes()==b"","dark source journal")
    typed(source["final_pixels"],[0]*1024); typed(source["final_keymap"],"00"*32)
    for k in ("initial_keymap","final_keymap"): typed(capture[k],"00"*32)
    frames=[json.loads(s) for s in (record/"frames.jsonl").read_text().splitlines()]
    waits=[json.loads(s) for s in (record/"waits.jsonl").read_text().splitlines()]
    typed(frames,capture["frames"]); require(len(frames)==len(waits)==8,"complete acquisition set")
    for index,f in enumerate(frames):
        typed(f["index"],index)
        typed(f["due_ns"],e+(index*120+case["offsets"][index%4]*10+5)*1_000_000)
        typed(waits[index],{k:f[k] for k in ("index","due_ns","pre","wait","post")})
        frame_valid(f)
        require(f["extracted_ns"]<=e+1_050_000_000,"source window")
