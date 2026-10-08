import os, json, hashlib, time, sys, platform
from pathlib import Path
import numpy as np
import torch
import torch.nn.functional as F

DATA_SEED=89100471; INIT_SEED=89100472; STEPS=1000; LR=0.2; THRESHOLD=0.75
CENTERS=((20,15),(8,8),(32,8),(8,22),(32,22))
HELD=((14,8),(26,8),(14,22),(26,22),(8,15),(20,25),(32,15),(20,8))
def sha(b): return hashlib.sha256(b).hexdigest()
def tiles(n,seed,centers,positive_size=9,negative_center=(4,4),negative_size=5,balanced=True):
 r=np.random.default_rng(seed); x=r.normal(0,.03,(n,1,30,40)).astype(np.float32); y=np.zeros(n,np.float32)
 for i in range(n):
  pos=i%2==0 if balanced else True; y[i]=float(pos)
  if pos: cx,cy=centers[(i//2)%len(centers)]; size=positive_size
  else: cx,cy=negative_center; size=negative_size
  h=size//2; x[i,0,cy-h:cy+h+1,cx-h:cx+h+1]+=.8
 return x,y
def dataset(seed):
 return (tiles(160,seed,CENTERS),tiles(80,seed+2,((20,15),)),{str(c):tiles(80,seed+10+i,(c,)) for i,c in enumerate(HELD)})
def init_np(seed,extent):
 r=np.random.default_rng(seed); k=r.normal(0,.04,(4,1,3,3)).astype(np.float32); b=np.zeros(4,np.float32); d=np.zeros(8 if extent else 4,np.float32); d[:4]=r.normal(0,.04,4).astype(np.float32); return k,b,d,np.float32(0)
class Model(torch.nn.Module):
 def __init__(self,seed,extent):
  super().__init__(); self.extent=extent; k,b,d,o=init_np(seed,extent)
  self.k=torch.nn.Parameter(torch.tensor(k,device='cuda')); self.b=torch.nn.Parameter(torch.tensor(b,device='cuda')); self.d=torch.nn.Parameter(torch.tensor(d,device='cuda')); self.o=torch.nn.Parameter(torch.tensor(o,device='cuda'))
 def forward(self,x):
  a=F.relu(F.conv2d(x,self.k,self.b)); m=a.amax((2,3)).flatten(1); q=torch.cat((m,a.mean((2,3)).flatten(1)),1) if self.extent else m; return q@self.d+self.o
def arrays(x,y): return torch.from_numpy(x).to('cuda'),torch.from_numpy(y).to('cuda')
def finite_difference_probe():
 torch.manual_seed(89100473); g=torch.Generator(device='cpu').manual_seed(89100473)
 x=torch.randn((2,1,8,9),generator=g,dtype=torch.float64).to('cuda'); y=torch.tensor([0.,1.],device='cuda',dtype=torch.float64)
 m=Model(INIT_SEED,True).double()
 params=[m.k,m.b,m.d,m.o]; logits=m(x); loss=F.binary_cross_entropy_with_logits(logits,y); grads=torch.autograd.grad(loss,params)
 checks=[]; eps=1e-5
 for pi,(p,grad) in enumerate(zip(params,grads)):
  flat=p.view(-1); gf=grad.view(-1)
  for idx in range(flat.numel()):
   old=float(flat[idx]); flat[idx]=old+eps; plus=F.binary_cross_entropy_with_logits(m(x),y).item()
   flat[idx]=old-eps; minus=F.binary_cross_entropy_with_logits(m(x),y).item()
   flat[idx]=old; numeric=(plus-minus)/(2*eps); analytic=float(gf[idx]); rel=abs(numeric-analytic)/max(1e-7,abs(numeric)+abs(analytic))
   checks.append(rel)
 return {'count':len(checks),'max_symmetric_relative_error':max(checks),'pass':len(checks)==49 and max(checks)<1e-4}
def main(out):
 out=Path(out); out.mkdir(parents=True,exist_ok=False)
 assert os.environ.get('CUBLAS_WORKSPACE_CONFIG')==':4096:8'
 torch.use_deterministic_algorithms(True); torch.backends.cudnn.deterministic=True; torch.backends.cudnn.benchmark=False; torch.backends.cuda.matmul.allow_tf32=False; torch.backends.cudnn.allow_tf32=False
 assert torch.are_deterministic_algorithms_enabled() and torch.backends.cudnn.deterministic and not torch.backends.cudnn.benchmark
 assert torch.cuda.is_available() and 'RTX 3080' in torch.cuda.get_device_name(0)
 torch.cuda.reset_peak_memory_stats(); fd=finite_difference_probe()
 if not fd['pass']: raise RuntimeError('STOP_FINITE_DIFFERENCE_GATE '+json.dumps(fd))
 tr,base,held=dataset(DATA_SEED); inp={'train_x':tr[0],'train_y':tr[1],'base_x':base[0],'base_y':base[1]}
 for i,key in enumerate(sorted(held)): inp[f'held_{i}_x'],inp[f'held_{i}_y']=held[key]
 np.savez_compressed(out/'INPUTS.npz',**inp)
 initial={}; trained={}; times={}; logits={}; tx,ty=arrays(*tr); bx,by=arrays(*base)
 for arm,extent in (('max_only',False),('max_mean',True)):
  m=Model(INIT_SEED,extent); initial[arm]=[p.detach().cpu().numpy().copy() for p in (m.k,m.b,m.d,m.o)]; start=time.perf_counter()
  for _ in range(STEPS):
   loss=F.binary_cross_entropy_with_logits(m(tx),ty); loss.backward()
   with torch.no_grad():
    for p in (m.k,m.b,m.d,m.o): p-=LR*p.grad; p.grad=None
  torch.cuda.synchronize(); times[arm]=time.perf_counter()-start; trained[arm]=[p.detach().cpu().numpy().copy() for p in (m.k,m.b,m.d,m.o)]
  cats={'train':tx,'base':bx}
  for i in range(8): cats[f'held_{i}']=arrays(inp[f'held_{i}_x'],inp[f'held_{i}_y'])[0]
  logits[arm]={}
  with torch.no_grad():
   for name,x in cats.items(): logits[arm][name]=m(x).cpu().numpy().astype(float).tolist()
 np.savez(out/'INITIAL_WEIGHTS.npz',**{f'{a}_{n}':v for a,vs in initial.items() for n,v in zip(('kernel','bias','dense','output_bias'),vs)})
 np.savez(out/'WEIGHTS.npz',**{f'{a}_{n}':v for a,vs in trained.items() for n,v in zip(('kernel','bias','dense','output_bias'),vs)})
 raw={'schema':'tiny-visual-extent-readout-cuda-v1','allocation':'tiny-visual-extent-readout-4817-cuda-20260927-02','data_seed':DATA_SEED,'init_seed':INIT_SEED,'steps':STEPS,'learning_rate':LR,'threshold':THRESHOLD,'held_centers':[list(c) for c in sorted(HELD)],'fit_seconds':times,'finite_difference_probe':fd,'logits':logits,'input_sha256':sha((out/'INPUTS.npz').read_bytes()),'initial_weights_sha256':sha((out/'INITIAL_WEIGHTS.npz').read_bytes()),'weights_sha256':sha((out/'WEIGHTS.npz').read_bytes()),'environment':{'python':sys.version,'platform':platform.platform(),'torch':torch.__version__,'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),'cublas_workspace_config':os.environ['CUBLAS_WORKSPACE_CONFIG'],'deterministic':torch.are_deterministic_algorithms_enabled(),'peak_allocated':torch.cuda.max_memory_allocated()},'formal_fits':0,'construction_fits':2}
 (out/'RAW.json').write_text(json.dumps(raw,sort_keys=True,separators=(',',':'))+'\n')
if __name__=='__main__': main(sys.argv[1])
