from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];PKG=ROOT/'research/doom/v39_v15_keymap_after_batch_a05_20261005'
def sha(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def audit():
 freeze=json.loads((PKG/'FREEZE.json').read_text(encoding='utf-8-sig'))
 stop=json.loads((PKG/'results/a01/RUN_FAILURE.json').read_text(encoding='utf-8-sig'))
 head=subprocess.run(['git','-C',str(ROOT),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip();errors=[]
 if subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',freeze['base_commit'],head],check=False).returncode:errors.append('freeze_not_ancestor')
 for rel,expected in freeze['source_sha256'].items():
  p=ROOT/rel
  if not p.is_file() or sha(p)!=expected:errors.append('source_hash:'+rel)
 if stop.get('candidate_invocations')!=1 or stop.get('candidate_completed') is not False:errors.append('candidate_count_or_status')
 if stop.get('status')!='STOP_FAKE_CLEANUP_DROP_ALIAS':errors.append('stop_status')
 if (PKG/'results/a01/RAW.json').exists():errors.append('unexpected_raw_after_failed_batch')
 return {'schema':'v39-v15-keymap-after-batch-stop-audit-v1','disposition':'PASS_STOP_PROVENANCE_ONLY' if not errors else 'FAIL','errors':errors,'freeze_base':freeze['base_commit'],'source_sha256_verified':len(freeze['source_sha256']),'raw_audit':'NOT_POSSIBLE_RAW_NOT_RETAINED','scope':'source-freeze and failure-record integrity only; does not restore missing case traces or prove a scientific gate'}
if __name__=='__main__':
 r=audit();(PKG/'results/AUDIT.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n',encoding='utf-8');print(json.dumps(r,sort_keys=True));raise SystemExit(bool(r['errors']))
