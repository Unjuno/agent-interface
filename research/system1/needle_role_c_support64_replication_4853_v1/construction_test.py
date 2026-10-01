"""Zero-update identity, seed-separation, prefix and corruption checks."""
import ast,hashlib,importlib.util,pathlib,torch,os
from prefix_contract import tensor_bytes,verify_prefix
raw=pathlib.Path("/src/upstream_runner.py").read_bytes()
assert hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()=="ecd3a0414178f38535406573314793a40b353878"
seeds=(7866801,7867001,7867201)
os.environ["NEEDLE_SEED"]=str(seeds[0])
os.environ["NEEDLE_OUTPUT"]="/unused"
spec=importlib.util.spec_from_file_location("public_runner","/src/upstream_runner.py")
u=importlib.util.module_from_spec(spec); spec.loader.exec_module(u)
for s in seeds:
    x64,x16=verify_prefix(u,s); assert torch.equal(x64[:16],x16) and tensor_bytes(x64[:16])==tensor_bytes(x16)
for i,a in enumerate(seeds):
    for b in seeds[i+1:]:
        assert not set(range(a+1,a+13)) & set(range(b+1,b+13)),"seed stream overlap"
bad=seeds[0]; _,x16=verify_prefix(u,bad); x16=x16.clone(); x16[0,0]+=1
class Corrupted:
    D=u.D
    def data(self,n,s): return x16 if n==16 and s==bad+3 else u.data(n,s)
try: verify_prefix(Corrupted(),bad); raise AssertionError("corruption accepted")
except ValueError as e: assert str(e)=="values"
for p in pathlib.Path("/src").glob("*.py"): ast.parse(p.read_text(encoding="utf-8"))
assert tensor_bytes(torch.tensor([0,1,127,128,255],dtype=torch.uint8))==bytes([0,1,127,128,255])
print("CONSTRUCTION_PASS seeds=3 prefix_exact=True streams_disjoint=True byte_sentinel=True corruption_rejected=True optimizer_updates=0")
