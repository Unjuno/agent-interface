import json,hashlib,sys
from pathlib import Path
import numpy as np
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def direct(x,k,b,d,o,extent):
 n,_,h,w=x.shape; a=np.zeros((n,h-2,w-2,4),np.float64)
 for r in range(h-2):
  for c in range(w-2):
   for f in range(4):
    v=float(b[f])
    for dy in range(3):
     for dx in range(3): v+=x[:,0,r+dy,c+dx].astype(np.float64)*float(k[f,0,dy,dx])
    a[:,r,c,f]=np.maximum(0,v)
 flat=a.reshape(n,-1,4); mx=flat.max(1); pooled=np.concatenate((mx,flat.mean(1)),1) if extent else mx
 return pooled@d.astype(np.float64)+float(o)
def main(root):
 p=Path(root); raw=json.loads((p/'RAW.json').read_text()); err=[]
 if raw.get('schema')!='tiny-visual-extent-readout-cuda-v1' or raw.get('allocation')!='tiny-visual-extent-readout-4817-cuda-20260927-02': err.append('identity')
 if raw.get('formal_fits')!=0 or raw.get('construction_fits')!=2 or raw.get('steps')!=1000 or raw.get('learning_rate')!=.2: err.append('protocol')
 if not raw.get('finite_difference_probe',{}).get('pass') or raw.get('finite_difference_probe',{}).get('count')!=49: err.append('finite_difference')
 for f,k in [('INPUTS.npz','input_sha256'),('WEIGHTS.npz','weights_sha256'),('INITIAL_WEIGHTS.npz','initial_weights_sha256')]:
  if sha(p/f)!=raw.get(k): err.append('hash:'+f)
 with np.load(p/'INPUTS.npz',allow_pickle=False) as X,np.load(p/'WEIGHTS.npz',allow_pickle=False) as W,np.load(p/'INITIAL_WEIGHTS.npz',allow_pickle=False) as I:
  if not np.array_equal(I['max_only_kernel'],I['max_mean_kernel']) or not np.array_equal(I['max_only_bias'],I['max_mean_bias']) or not np.array_equal(I['max_only_dense'],I['max_mean_dense'][:4]) or np.any(I['max_mean_dense'][4:]!=0): err.append('initial_weights')
  for arm,ext in [('max_only',False),('max_mean',True)]:
   cats={'train':('train_x','train_y'),'base':('base_x','base_y')}
   cats.update({f'held_{i}':(f'held_{i}_x',f'held_{i}_y') for i in range(8)})
   for name,(xk,yk) in cats.items():
    z=direct(X[xk],W[arm+'_kernel'],W[arm+'_bias'],W[arm+'_dense'],W[arm+'_output_bias'],ext)
    saved=np.asarray(raw['logits'][arm][name],float)
    if z.shape!=saved.shape or not np.allclose(z,saved,rtol=1e-5,atol=1e-5): err.append(f'logits:{arm}:{name}')
 def met(arm,cat):
  with np.load(p/'INPUTS.npz',allow_pickle=False) as X: y=X['train_y' if cat=='train' else 'base_y' if cat=='base' else cat+'_y']
  z=np.asarray(raw['logits'][arm][cat]); pr=1/(1+np.exp(-np.clip(z,-30,30)))
  return float(np.mean((pr>=.5)==y)),float(np.mean(pr[y==1]>=.75)),float(np.mean(pr[y==0]>=.75))
 tr=met('max_mean','train')[0]; base=met('max_mean','base')[0]; hp=[met('max_mean',f'held_{i}')[1] for i in range(8)]; hn=[met('max_mean',f'held_{i}')[2] for i in range(8)]; bp=[met('max_only',f'held_{i}')[1] for i in range(8)]
 decision='STOP_PROVENANCE_OR_AUDIT' if err else ('STOP_NO_CONSTRUCTION_COMPETENCE' if tr<.95 or base<.95 or np.mean(hp)<.9 or np.mean(hn)>.01 else ('HOLD_READOUT_NOT_DISCRIMINATING' if np.mean(bp)>=.7 else 'PASS_EXTENT_READOUT_CONSTRUCTION_SCOPED'))
 result={'errors':err,'integrity_pass':not err,'decision':decision,'max_mean_train_accuracy':tr,'max_mean_base_accuracy':base,'max_mean_held_positive_accept_mean':float(np.mean(hp)),'max_mean_held_negative_false_accept_mean':float(np.mean(hn)),'max_only_held_positive_accept_mean':float(np.mean(bp))}
 (p/'AUDIT.json').write_text(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n'); print(json.dumps(result,sort_keys=True)); return 0 if not err else 2
if __name__=='__main__': raise SystemExit(main(sys.argv[1]))
