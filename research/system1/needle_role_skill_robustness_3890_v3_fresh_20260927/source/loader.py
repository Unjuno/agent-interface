"""Independent data-only artifact validator/loader; no dynamic code or torch.load."""
import hashlib,json,os,sys,copy,tempfile
import torch
SCHEMA="unjuno.role-skill.numeric-json.v1"
EXPECTED_KEYS={"A":{"enc.0.weight","enc.0.bias","head.weight","head.bias"},"B":{"core.enc.0.weight","core.enc.0.bias","core.head.weight","core.head.bias","a","b"},"C":{"core.enc.0.weight","core.enc.0.bias","core.head.weight","core.head.bias","a","b"}}
SHAPES={"enc.0.weight":[16,8],"enc.0.bias":[16],"head.weight":[4,16],"head.bias":[4],"core.enc.0.weight":[16,8],"core.enc.0.bias":[16],"core.head.weight":[4,16],"core.head.bias":[4],"a":[16,2],"b":[2,4]}
def canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def validate(path,expected):
    raw=open(path,"rb").read(); obj=json.loads(raw)
    if set(obj)!={"schema","generation","architecture","graph","provenance","tensors","payload_sha256"}: raise ValueError("schema_keys")
    if obj["schema"]!=SCHEMA: raise ValueError("schema")
    if obj["generation"]!=expected["seed"]: raise ValueError("generation")
    if obj["architecture"]!={"input":8,"hidden":16,"classes":4,"rank":2,"roles":["A","B","C"]}: raise ValueError("architecture")
    if obj["graph"]!={"nodes":[{"id":r,"version":r+"-v1"} for r in ("A","B","C")],"edges":[["A","B"],["B","C"]],"scope":"synthetic-fixture-v1"}: raise ValueError("graph_manifest")
    if obj["provenance"]!={"allocation":"needle-role-skill-cross-process-reload-v1","predecessor_issue":3780,"seed":expected["seed"],"family":"synthetic-role-adapter-v1"}: raise ValueError("provenance")
    digest=obj.pop("payload_sha256")
    if hashlib.sha256(canonical(obj)).hexdigest()!=digest: raise ValueError("digest")
    if set(obj["tensors"])!={"A","B","C"}: raise ValueError("roles")
    for role,st in obj["tensors"].items():
        if set(st)!=EXPECTED_KEYS[role]: raise ValueError("tensor_keys")
        for k,v in st.items():
            def shape(z): return [len(z),*shape(z[0])] if isinstance(z,list) and z else ([] if z==[] else [])
            if shape(v)!=SHAPES[k]: raise ValueError("tensor_shape")
            def numbers(z):
                if isinstance(z,list): return all(numbers(q) for q in z)
                return type(z) in (int,float) and abs(z)<1e6
            if not numbers(v): raise ValueError("tensor_value")
    obj["payload_sha256"]=digest
    return obj,hashlib.sha256(raw).hexdigest()

class Graph:
    def __init__(self,g): self.generation=g; self.cursor="A"; self.accepted=set(); self.emissions=0
    def step(self,source,target,generation,receipt_id,version,verified=True,scope="synthetic-fixture-v1"):
        valid=(source==self.cursor and target in {"A":["B"],"B":["C"],"C":[]}[self.cursor] and generation==self.generation and receipt_id not in self.accepted and version==source+"-v1" and verified is True and scope=="synthetic-fixture-v1")
        if not valid:return "YIELD"
        self.accepted.add(receipt_id); self.cursor=target; self.emissions+=1; return "ADVANCE"
    def state(self): return (self.cursor,self.generation,tuple(sorted(self.accepted)),self.emissions)

def infer(artifact,role,rows):
    state=artifact["tensors"][role]
    def t(k): return torch.tensor(state[k],dtype=torch.float32)
    x=torch.tensor(rows,dtype=torch.float32)
    if role=="A":
        h=torch.tanh(torch.nn.functional.linear(x,t("enc.0.weight"),t("enc.0.bias")))
        y=torch.nn.functional.linear(h,t("head.weight"),t("head.bias"))
    else:
        h=torch.tanh(torch.nn.functional.linear(x,t("core.enc.0.weight"),t("core.enc.0.bias")))
        y=torch.nn.functional.linear(h,t("core.head.weight"),t("core.head.bias"))+h@t("a")@t("b")/2
    return y.argmax(-1).tolist()

def exercise(artifact,expected,generation):
    graph=Graph(generation); initial=graph.state(); controls={}
    bad=[("wrong_adapter_version",("A","B",generation,"ver","A-v0",True,"synthetic-fixture-v1")),("skipped_edge",("A","C",generation,"skip","A-v1",True,"synthetic-fixture-v1")),("wrong_scope",("A","B",generation,"scope","A-v1",True,"other")),("unverified_outcome",("A","B",generation,"unverified","A-v1",False,"synthetic-fixture-v1")),("unknown_destination",("A","Z",generation,"unknown","A-v1",True,"synthetic-fixture-v1"))]
    for name,args in bad:
        before=graph.state(); controls[name]=graph.step(*args); assert graph.state()==before==initial
    for name,mutate in (("tampered_digest",lambda o:o.update(payload_sha256="0"*64)),("unknown_schema",lambda o:o.update(schema="unknown"))):
        probe=json.loads(json.dumps(artifact)); mutate(probe)
        with tempfile.NamedTemporaryFile("w",encoding="utf-8",delete=False) as f: json.dump(probe,f); path=f.name
        try:
            try: validate(path,expected); controls[name]="ACCEPT"
            except Exception: controls[name]="YIELD"
        finally: os.unlink(path)
    with tempfile.NamedTemporaryFile("wb",delete=False) as f: f.write(b'{"schema":'); path=f.name
    try:
        try: json.load(open(path)); controls["truncated"]="ACCEPT"
        except Exception: controls["truncated"]="YIELD"
    finally: os.unlink(path)
    # Accepted receipt repeated must be rejected without a second mutation.
    controls["duplicate_receipt"]=graph.step("A","B",generation,"dup","A-v1"); state=graph.state(); controls["duplicate_receipt_second"]=graph.step("B","C",generation,"dup","B-v1"); assert graph.state()==state
    graph=Graph(generation); old=graph.step("A","B",generation-1,"old","A-v1"); assert old=="YIELD"
    flow=[graph.step("A","B",generation,"a-"+str(generation),"A-v1"),graph.step("B","C",generation,"b-"+str(generation),"B-v1")]
    return {"generation":generation,"controls":controls,"flow":flow,"cursor":graph.cursor,"old_receipt":"YIELD","fixture_emissions":graph.emissions}
if __name__=="__main__":
    try:
        artifact,sha=validate(sys.argv[1],json.load(open(sys.argv[2],encoding="utf-8")))
        expected=json.load(open(sys.argv[2],encoding="utf-8"));pred={r:infer(artifact,r,expected["roles"][r]["inputs"]) for r in ("A","B","C")}
        graphs=[exercise(artifact,expected,g) for g in (artifact["generation"],artifact["generation"]+1)]
        json.dump({"accepted":True,"artifact_sha256":sha,"predictions":pred,"graphs":graphs},open(sys.argv[3],"w",encoding="utf-8"),sort_keys=True)
    except Exception as e:
        json.dump({"accepted":False,"error":repr(e),"type":type(e).__name__},open(sys.argv[3],"w",encoding="utf-8"),sort_keys=True)


