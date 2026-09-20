"""Independent data-only artifact validator/loader; no dynamic code or torch.load."""
import hashlib,json,os,sys
SCHEMA="unjuno.role-skill.numeric-json.v1"
EXPECTED_KEYS={"A":{"enc.0.weight","enc.0.bias","head.weight","head.bias"},"B":{"core.enc.0.weight","core.enc.0.bias","core.head.weight","core.head.bias","a","b"},"C":{"core.enc.0.weight","core.enc.0.bias","core.head.weight","core.head.bias","a","b"}}
SHAPES={"enc.0.weight":[16,8],"enc.0.bias":[16],"head.weight":[4,16],"head.bias":[4],"core.enc.0.weight":[16,8],"core.enc.0.bias":[16],"core.head.weight":[4,16],"core.head.bias":[4],"a":[16,2],"b":[2,4]}
def canonical(x): return json.dumps(x,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def validate(path,expected):
    raw=open(path,"rb").read(); obj=json.loads(raw)
    if set(obj)!={"schema","generation","architecture","tensors","payload_sha256"}: raise ValueError("schema_keys")
    if obj["schema"]!=SCHEMA: raise ValueError("schema")
    if obj["generation"]!=expected["seed"]: raise ValueError("generation")
    if obj["architecture"]!={"input":8,"hidden":16,"classes":4,"rank":2,"roles":["A","B","C"]}: raise ValueError("architecture")
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
if __name__=="__main__":
    try:
        artifact,sha=validate(sys.argv[1],json.load(open(sys.argv[2],encoding="utf-8")))
        json.dump({"accepted":True,"artifact_sha256":sha,"roles":sorted(artifact["tensors"])},open(sys.argv[3],"w",encoding="utf-8"),sort_keys=True)
    except Exception as e:
        json.dump({"accepted":False,"error":str(e)},open(sys.argv[3],"w",encoding="utf-8"),sort_keys=True)
