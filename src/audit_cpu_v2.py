import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
EXPECTED_RUN_BLOB='ac2deba1b8e4f99a252e375a911d9603a55c3d29'
EXPECTED_BASE_AUDIT_BLOB='0bdf8561f1a37c6c1e0f4c78323f4048e3274716'
EXPECTED_RAW_SHA='7f721644095c903979a7e2d06a6e5e884c692d8245a1b2f0c65cfc9871bd1b70'
EXPECTED_RAW_KEYS={'allocation','construction_fits','data_seed','environment','finite_difference_probe','fit_seconds','formal_fits','held_centers','init_seed','initial_weights_sha256','input_sha256','learning_rate','logits','schema','steps','threshold','weights_sha256'}
def sha(b): return hashlib.sha256(b).hexdigest()
def gitblob(p):
 b=Path(p).read_bytes(); return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def main(result,src):
 result=Path(result); src=Path(src); errors=[]
 raw_bytes=(result/'RAW.json').read_bytes()
 raw=json.loads(raw_bytes.decode('utf-8'))
 if sha(raw_bytes)!=EXPECTED_RAW_SHA: errors.append('raw_sha256')
 freeze=json.loads((src/'FREEZE.json').read_text(encoding='utf-8'))
 if freeze.get('posthoc_raw_sha256')!=EXPECTED_RAW_SHA: errors.append('freeze_raw_source_id')
 if set(raw)!=EXPECTED_RAW_KEYS: errors.append('raw_key_set')
 if raw.get('schema')!='tiny-visual-extent-readout-cuda-v1' or raw.get('allocation')!='tiny-visual-extent-readout-4817-cuda-20260927-03': errors.append('identity')
 if raw.get('data_seed')!=89100471 or raw.get('init_seed')!=89100472: errors.append('seeds')
 if raw.get('steps')!=1000 or raw.get('learning_rate')!=0.2 or raw.get('threshold')!=0.75: errors.append('frozen_protocol')
 if raw.get('formal_fits')!=0 or raw.get('construction_fits')!=2: errors.append('fit_counts')
 fd=raw.get('finite_difference_probe',{})
 if not fd.get('pass') or fd.get('count')!=49 or fd.get('max_symmetric_relative_error',1)>=1e-4: errors.append('finite_difference')
 ft=raw.get('fit_seconds',{})
 if set(ft)!={'max_only','max_mean'} or any(not isinstance(v,(int,float)) or not np.isfinite(v) or v<0 for v in ft.values()): errors.append('fit_seconds')
 env=raw.get('environment',{})
 if env.get('cublas_workspace_config')!=':4096:8' or env.get('deterministic') is not True or 'RTX 3080' not in env.get('gpu',''): errors.append('runtime_identity')
 if freeze.get('corrected_runner_blob')!=EXPECTED_RUN_BLOB or freeze.get('cpu_auditor_blob')!=EXPECTED_BASE_AUDIT_BLOB: errors.append('freeze_source_ids')
 if gitblob(src/'run_cuda.py')!=EXPECTED_RUN_BLOB or gitblob(src/'audit_cpu.py')!=EXPECTED_BASE_AUDIT_BLOB: errors.append('local_source_blob')
 for name,key in [('WEIGHTS.npz','weights_sha256'),('INITIAL_WEIGHTS.npz','initial_weights_sha256')]:
  if not (result/name).is_file() or sha((result/name).read_bytes())!=raw.get(key): errors.append('hash:'+name)
 regen_sha=None
 with tempfile.TemporaryDirectory(prefix='extent-rebuild-',dir='/tmp') as td:
  regen=subprocess.run([sys.executable,str(src/'rebuild_inputs.py'),str(Path(td)/'rebuilt')],capture_output=True,text=True)
  if regen.returncode: errors.append('regenerator_exit')
  else:
   rebuilt=Path(td)/'rebuilt'/'INPUTS.npz'; regen_sha=sha(rebuilt.read_bytes())
   if regen_sha!=raw.get('input_sha256'): errors.append('regenerated_input_hash')
   if (result/'INPUTS.npz').exists() and (result/'INPUTS.npz').read_bytes()!=rebuilt.read_bytes(): errors.append('retained_input_mismatch')
   work=Path(td)/'audit-work'; work.mkdir()
   for name in ('RAW.json','WEIGHTS.npz','INITIAL_WEIGHTS.npz'): shutil.copy2(result/name,work/name)
   shutil.copy2(rebuilt,work/'INPUTS.npz')
   expected=json.loads((result/'AUDIT.json').read_text())
   base=subprocess.run([sys.executable,str(src/'audit_cpu.py'),str(work)],capture_output=True,text=True)
   if base.returncode!=0: errors.append('base_auditor_exit')
   got=json.loads((work/'AUDIT.json').read_text()) if (work/'AUDIT.json').exists() else {}
   if got.get('errors')!=[] or got.get('integrity_pass') is not True: errors.append('base_auditor_errors')
   if got!=expected: errors.append('archived_audit_mismatch')
 out={'schema':'extent-readout-posthoc-audit-v2','integrity_pass':not errors,'errors':errors,'reconstructed_input_sha256':regen_sha,'numpy':np.__version__,'decision':'PASS_RAW_RECONSTRUCTION_AND_METADATA_V2' if not errors else 'HOLD_POSTHOC_AUDIT_V2'}
 (result/'AUDIT_V2.json').write_text(json.dumps(out,sort_keys=True,separators=(',',':'))+'\n')
 print(json.dumps(out,sort_keys=True)); return 0 if not errors else 2
if __name__=='__main__': raise SystemExit(main(sys.argv[1],sys.argv[2]))

