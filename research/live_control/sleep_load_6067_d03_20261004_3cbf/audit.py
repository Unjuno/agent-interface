"""Saved-only D03 auditor; imports no acquisition."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
from core import validate_cell,integer

def median(values):
    v=sorted(values);n=len(v)
    return v[n//2] if n%2 else (v[n//2-1]+v[n//2])/2

def decode(data):
    def pairs(items):
        out={}
        for key,value in items:
            if key in out:raise ValueError('duplicate JSON key')
            out[key]=value
        return out
    return json.loads(data,object_pairs_hook=pairs)

def buffers(raw,plan):
    expected={"runtime.json","result.json"}|{s["id"]+".json" for s in plan["cases"]}
    if {p.name for p in raw.iterdir()}!=expected or any(p.is_symlink() or not p.is_file() for p in raw.iterdir()):raise ValueError("closed raw schema")
    return {name:(raw/name).read_bytes() for name in sorted(expected)}

def evaluate(raw,plan,hashes):
    return evaluate_buffers(buffers(raw,plan),plan,hashes)

def evaluate_buffers(saved,plan,hashes):
    runtime=decode(saved['runtime.json']);result=decode(saved['result.json'])
    limits={"cpu.max":"100000 100000","memory.max":"536870912","memory.swap.max":"0","pids.max":"64"}
    if runtime["source_sha256"]!=hashes or runtime["limits"]!=limits or type(runtime["uid"]) is not int or runtime["uid"]!=501:raise ValueError("source/resource custody")
    pid=integer(runtime["pid"])
    if pid<=0:raise ValueError("parent PID")
    metrics=[];last_end=0;prior=None
    for spec in plan["cases"]:
        cell=decode(saved[spec['id']+'.json'])
        if type(cell["pid"]) is not int or cell["pid"]!=pid or cell["start_ns"]<last_end:raise ValueError("study PID/order")
        metrics.append(validate_cell(cell,spec,plan));last_end=cell["end_ns"]
        first,last=cell['rows'][0]['pre'],cell['rows'][-1]['post']
        if prior and (first['process_cpu_ns']<prior['process_cpu_ns'] or set(first['cpu'])!=set(prior['cpu']) or any(first['cpu'][k]<prior['cpu'][k] for k in prior['cpu'])):raise ValueError('crosscell counter continuity')
        prior=last
    by={(m["pair"],m["arm"]):m for m in metrics}
    differences=[median(by[p,"loaded"]["delays"])-median(by[p,"quiet"]["delays"]) for p in range(6)]
    pooled=median([x for m in metrics if m["arm"]=="loaded" for x in m["delays"]])-median([x for m in metrics if m["arm"]=="quiet" for x in m["delays"]])
    n=sum(d>=1_000_000 for d in differences)
    pressure=all(by[p,"loaded"]["throttle_count"]>0 and by[p,"loaded"]["throttle_usec"]>0 for p in range(6))
    d={"status":"SUPPORT_IMPOSED_LOAD_ONLY" if pooled>=1_000_000 and n>=5 and pressure else "HOLD_NOT_SUPPORTED","pooled_ns":pooled,"paired_ns":differences,"qualifying_pairs":n,"all_loaded_pressure":pressure}
    if result!={"allocation":plan["allocation"],"status":"COMPLETE","cells":12,"error":None,"decision":d,"source_unchanged":True}:raise ValueError("producer decision independent join")
    return d

def audit_runtime(reader=None,uid=None):
    reader=reader or (lambda k:Path('/sys/fs/cgroup/'+k).read_text().strip())
    uid=os.getuid() if uid is None else uid
    limits={k:reader(k) for k in ('cpu.max','memory.max','memory.swap.max','pids.max')}
    expected={'cpu.max':'100000 100000','memory.max':'536870912','memory.swap.max':'0','pids.max':'64'}
    if type(uid) is not int or uid!=501 or limits!=expected:raise ValueError('actual audit resources')
    return {'uid':uid,'limits':limits,'pid':os.getpid()}

def run(raw,source,out):
    out.mkdir(exist_ok=False)
    runtime=audit_runtime()
    (out/'runtime.json').write_text(json.dumps(runtime,sort_keys=True)+'\n')
    freeze=decode((source/"FREEZE.json").read_bytes())
    hashes={k:hashlib.sha256((source/k).read_bytes()).hexdigest() for k in freeze["source_sha256"]}
    if hashes!=freeze["source_sha256"]:raise ValueError("auditor frozen source")
    plan=decode((source/"plan.json").read_bytes())
    saved=buffers(raw,plan)
    d=evaluate_buffers(saved,plan,hashes)
    spec=next(s for s in plan["cases"] if s["arm"]=="loaded")
    original=decode(saved[spec['id']+'.json'])
    controls=[]
    mutations=[
        ("drop-row",lambda c:c["rows"].pop()),
        ("request",lambda c:c["rows"][0].update(requested_ns=1)),
        ("clock",lambda c:c["rows"][0].update(return_ns=0)),
        ("counter",lambda c:c["rows"][0]["pre"]["cpu"].update(usage_usec=0)),
        ("child-exit",lambda c:c["children"][0].update(exit_code=2)),
        ("foreign-pid",lambda c:c["rows"][0].update(pid=999999999)),
    ]
    for name,mutate in mutations:
        bad=copy.deepcopy(original);mutate(bad)
        data=json.dumps(bad,sort_keys=True)+"\n"
        (out/(name+".json")).write_text(data)
        try:validate_cell(bad,spec,plan)
        except (ValueError,KeyError,TypeError) as e:controls.append({"name":name,"status":"REJECTED","reason":str(e),"sha256":hashlib.sha256(data.encode()).hexdigest()})
        else:raise ValueError("control accepted:"+name)
    if buffers(raw,plan)!=saved:raise ValueError('raw changed during audit')
    if {k:hashlib.sha256((source/k).read_bytes()).hexdigest() for k in hashes}!=hashes:raise ValueError('source changed during audit')
    result={"status":"PASS_SAVED_DIAGNOSTIC_AUDIT","decision":d,"controls":controls,"raw_sha256":{k:hashlib.sha256(v).hexdigest() for k,v in saved.items()},"source_sha256":hashes,'audit_runtime':runtime}
    (out/"result.json").write_text(json.dumps(result,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"decision":d,"controls":len(controls)}))
    return 0

if __name__=="__main__":
    if len(sys.argv)!=4:raise SystemExit("usage: audit.py RAW SOURCE NEW_OUT")
    sys.exit(run(*(Path(p) for p in sys.argv[1:])))
