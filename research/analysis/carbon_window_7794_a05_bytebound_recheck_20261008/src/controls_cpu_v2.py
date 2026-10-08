import copy,json,shutil,subprocess,sys,tempfile
from pathlib import Path
def main(result,src):
 result=Path(result); src=Path(src)
 orig=json.loads((result/'RAW.json').read_text()); rows=[]
 muts=('alter_logit','drop_center','change_allocation','change_seed','change_step_count','negative_fit_time','inject_source_hash','corrupt_input_bytes')
 for name in muts:
  with tempfile.TemporaryDirectory(prefix='extent-mutation-',dir='/tmp') as td:
   t=Path(td); work=t/'result'; work.mkdir()
   for f in ('RAW.json','INPUTS.npz','WEIGHTS.npz','INITIAL_WEIGHTS.npz','AUDIT.json'): shutil.copy2(result/f,work/f)
   raw=copy.deepcopy(orig)
   if name=='alter_logit': raw['logits']['max_mean']['held_0'][0]+=0.01
   elif name=='drop_center': raw['logits']['max_mean'].pop('held_7')
   elif name=='change_allocation': raw['allocation']='wrong'
   elif name=='change_seed': raw['data_seed']+=1
   elif name=='change_step_count': raw['steps']-=1
   elif name=='negative_fit_time': raw['fit_seconds']['max_mean']=-1
   elif name=='inject_source_hash': raw['source_sha256']={'run_cuda.py':'0'*64}
   elif name=='corrupt_input_bytes': (work/'INPUTS.npz').write_bytes((work/'INPUTS.npz').read_bytes()+b'x')
   (work/'RAW.json').write_text(json.dumps(raw,sort_keys=True,separators=(',',':'))+'\n')
   p=subprocess.run([sys.executable,str(src/'audit_cpu_v2.py'),str(work),str(src)],capture_output=True,text=True)
   rows.append({'mutation':name,'rejected':p.returncode!=0,'exit':p.returncode})
 out={'schema':'extent-readout-posthoc-corruption-controls-v2','rejected':sum(r['rejected'] for r in rows),'total':len(rows),'pass_all':all(r['rejected'] for r in rows),'controls':rows}
 (result/'CONTROL_RESULTS_V2.json').write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n')
 print(json.dumps(out,sort_keys=True)); return 0 if out['pass_all'] else 2
if __name__=='__main__': raise SystemExit(main(sys.argv[1],sys.argv[2]))

