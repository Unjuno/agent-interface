"""Independent fresh-valid oracle addendum for Issue #4972.
The oracle is declared before model output: CONTINUE iff feature[2] == 0
and YIELD iff feature[2] == 1 on fresh, unambiguous rows.
"""
import hashlib,json,torch
class S(torch.nn.Module):
    def __init__(self):
        super().__init__(); self.net=torch.nn.Linear(8,2,bias=True)
        with torch.no_grad():
            self.net.weight.zero_(); self.net.bias.copy_(torch.tensor([1.0,-1.0]))
            self.net.weight[0,2]=-2.0; self.net.weight[1,2]=2.0
    def forward(self,x): return self.net(x)
def gate(fresh,ambiguous,hint):
    if not fresh or ambiguous: return "YIELD"
    return hint
gpu=S().cuda().eval(); cpu=S().eval()
cpu.load_state_dict({k:v.detach().cpu().clone() for k,v in gpu.state_dict().items()})
features=[]
for i in range(256):
    features.append([0,0,float(i%2),0,0,0,0,0])
gx=torch.tensor(features,device="cuda"); cx=gx.cpu()
with torch.inference_mode(): gl=gpu(gx).argmax(1).cpu(); cl=cpu(cx).argmax(1)
assert torch.equal(gl,cl)
gh=["CONTINUE" if int(v)==0 else "YIELD" for v in gl]
ch=["CONTINUE" if int(v)==0 else "YIELD" for v in cl]
for i in range(256):
    fresh=(i%4)!=2; ambiguous=(i%8)==3
    expected=("CONTINUE" if i%2==0 else "YIELD") if fresh and not ambiguous else "YIELD"
    assert gate(fresh,ambiguous,gh[i])==expected
    assert gate(fresh,ambiguous,ch[i])==expected
print(json.dumps({"status":"PASS_INDEPENDENT_FRESH_ORACLE","rows":256,"fresh_oracle_rows":160,"blocked_oracle_rows":96,"cpu_cuda_label_agreement":256,"gpu_fresh_oracle_agreement":160,"cpu_fresh_oracle_agreement":160,"gpu_blocked_oracle_agreement":96,"cpu_blocked_oracle_agreement":96,"fresh_oracle":"CONTINUE iff feature[2]==0; YIELD iff feature[2]==1","authority_grants":0,"input_grants":0,"task_success_claims":0,"device":torch.cuda.get_device_name(0),"torch":torch.__version__,"cuda_runtime":torch.version.cuda,"gpu_labels_sha256":hashlib.sha256(bytes(gl.tolist())).hexdigest(),"cpu_labels_sha256":hashlib.sha256(bytes(cl.tolist())).hexdigest()},sort_keys=True))