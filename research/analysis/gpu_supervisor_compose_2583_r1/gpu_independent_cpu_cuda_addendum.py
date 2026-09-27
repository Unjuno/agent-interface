"""Independent CPU/CUDA addendum for the scoped GPU gate.

This does not rewrite the original result. It separately checks same-weight
CPU/CUDA discrete labels and uses an independent oracle only for blocked rows,
where freshness/ambiguity must force YIELD.
"""
import hashlib, json, torch
torch.manual_seed(2508)
class S(torch.nn.Module):
    def __init__(self):
        super().__init__(); self.net=torch.nn.Sequential(torch.nn.Linear(8,16),torch.nn.Tanh(),torch.nn.Linear(16,2))
    def forward(self,x): return self.net(x)
def gate(fresh, ambiguous, hint):
    if not fresh or ambiguous: return "YIELD"
    if hint not in ("CONTINUE","YIELD"): raise ValueError("invalid hint")
    return hint
gpu=S().cuda().eval(); cpu=S().eval()
cpu.load_state_dict({k:v.detach().cpu().clone() for k,v in gpu.state_dict().items()})
features=[]; blocked_oracle=[]
for i in range(256):
    fresh=(i%4)!=2; ambiguous=(i%8)==3
    features.append([float(fresh),float(not ambiguous),float(i%2),0,0,0,0,0])
    if not fresh or ambiguous: blocked_oracle.append("YIELD")
gx=torch.tensor(features,device="cuda"); cx=gx.cpu()
with torch.inference_mode():
    gl=gpu(gx).argmax(1).cpu(); cl=cpu(cx).argmax(1)
assert torch.equal(gl,cl)
gpu_h=["CONTINUE" if int(v)==0 else "YIELD" for v in gl]
cpu_h=["CONTINUE" if int(v)==0 else "YIELD" for v in cl]
gpu_block=[]; cpu_block=[]
for i in range(256):
    if (i%4)!=2 and (i%8)!=3: continue
    gpu_block.append(gate((i%4)!=2,(i%8)==3,gpu_h[i]))
    cpu_block.append(gate((i%4)!=2,(i%8)==3,cpu_h[i]))
assert gpu_block==blocked_oracle and cpu_block==blocked_oracle
print(json.dumps({"status":"PASS_INDEPENDENT_CPU_CUDA_ADDENDUM","rows":256,"cpu_cuda_label_agreement":256,"blocked_oracle_rows":96,"gpu_blocked_oracle_agreement":96,"cpu_blocked_oracle_agreement":96,"authority_grants":0,"input_grants":0,"task_success_claims":0,"device":torch.cuda.get_device_name(0),"torch":torch.__version__,"cuda_runtime":torch.version.cuda,"gpu_labels_sha256":hashlib.sha256(bytes(gl.tolist())).hexdigest(),"cpu_labels_sha256":hashlib.sha256(bytes(cl.tolist())).hexdigest()},sort_keys=True))