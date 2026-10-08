"""Zero-update construction tests for Issue #4853."""
import ast,importlib.util,hashlib,os,pathlib,torch
spec=importlib.util.spec_from_file_location("public_runner","/src/upstream_runner.py")
u=importlib.util.module_from_spec(spec); spec.loader.exec_module(u)
from prefix_contract import tensor_bytes,verify_prefix
seed=7866401
assert os.environ.get("NEEDLE_SEED")==str(seed),"allocation"
raw=pathlib.Path("/src/upstream_runner.py").read_bytes()
assert hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()=="ecd3a0414178f38535406573314793a40b353878","runner_blob"
for name in ("paired.py","prefix_contract.py","audit.py"):
    ast.parse((pathlib.Path("/src")/name).read_text(encoding="utf-8"))
xs=bytes([0,1,127,128,255]); assert tensor_bytes(torch.tensor([0,1,127,128,255],dtype=torch.uint8))==xs,"sentinel_bytes"
x64,x16=verify_prefix(u,seed)
bad=x16.clone(); bad[0,0]=bad[0,0]+1
class Corrupted:
    D=u.D
    def data(self,n,s): return bad if n==16 and s==seed+3 else u.data(n,s)
try:
    verify_prefix(Corrupted(),seed)
    raise AssertionError("corruption_accepted")
except ValueError as e:
    assert str(e)=="values"
assert not torch.equal(x64[:16],bad) and tensor_bytes(x64[:16])!=tensor_bytes(bad)
print("CONSTRUCTION_PASS", "seed=7866401", "prefix_exact=True", "sentinel_bytes=True", "corrupted_prefix_rejected=True", "optimizer_updates=0")

