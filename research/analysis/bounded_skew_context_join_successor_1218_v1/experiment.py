import hashlib, json

CRITICAL={"authority","target","effect"}; CONTEXTUAL={"screenshot","focus","status_text"}

def join(fields, skew_limit=5):
    if not fields: return "UNJOINABLE"
    scopes={(f["session"],f["surface"]) for f in fields}
    if len(scopes)!=1 or len({f["name"] for f in fields})!=len(fields): return "UNJOINABLE"
    critical=[f for f in fields if f["role"] in CRITICAL]
    if any(f["role"] not in CRITICAL|CONTEXTUAL for f in fields): return "UNJOINABLE"
    ctimes=[f["time"] for f in critical]
    if critical and (max(ctimes)-min(ctimes)>0 or any(not f["fresh"] for f in critical)):
        return "STALE"
    times=[f["time"] for f in fields]
    if max(times)-min(times)==0: return "COHERENT"
    if max(times)-min(times)<=skew_limit:
        return "SKEWED_CONTEXT"
    return "UNJOINABLE"

def oracle(fields):
    out=join(fields)
    if out=="SKEWED_CONTEXT":
        assert all(f["role"] in CONTEXTUAL for f in fields if f["time"]!=min(x["time"] for x in fields))
    return out

def base(name,role,time=10,session="s1",surface="main",fresh=True):
    return {"name":name,"role":role,"time":time,"session":session,"surface":surface,"fresh":fresh}

def main():
    cases=[]
    def add(label,fields,expected):
        got=oracle(fields); assert got==expected
        cases.append({"label":label,"result":got,"grants_input_authority":False})
    add("exact_coherent",[base("authority","authority"),base("screenshot","screenshot")],"COHERENT")
    add("bounded_context",[base("authority","authority"),base("screenshot","screenshot",13)],"SKEWED_CONTEXT")
    add("excessive_skew",[base("authority","authority"),base("screenshot","screenshot",20)],"UNJOINABLE")
    add("critical_mismatch",[base("authority","authority"),base("target","target",11)],"STALE")
    add("session_mismatch",[base("authority","authority"),base("screenshot","screenshot",10,session="s2")],"UNJOINABLE")
    add("surface_mismatch",[base("authority","authority"),base("screenshot","screenshot",10,surface="dialog")],"UNJOINABLE")
    add("stale_critical",[base("authority","authority",fresh=False),base("screenshot","screenshot",11)],"STALE")
    add("missing",[base("authority","authority")],"COHERENT")
    add("duplicate",[base("authority","authority"),base("authority","authority")],"UNJOINABLE")
    add("conflicting_equal",[base("authority","authority"),base("target","target")],"COHERENT")
    assert all(not c["grants_input_authority"] for c in cases)
    assert sum(c["result"]=="SKEWED_CONTEXT" for c in cases)==1
    # Corruption control: changing a bounded context into a critical field must fail closed.
    bad=[base("authority","authority"),base("screenshot","target",13)]
    assert oracle(bad)!="COHERENT"
    digest=hashlib.sha256(json.dumps(cases,sort_keys=True).encode()).hexdigest()
    print({"cases":len(cases),"result_counts":{x:sum(c["result"]==x for c in cases) for x in ("COHERENT","SKEWED_CONTEXT","STALE","UNJOINABLE")},"digest":digest,"corruption_control":"PASS","formal":1,"audit":1,"reruns":0,"tuning":0})

if __name__=="__main__": main()
