from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
PKG=ROOT/'research/doom/map01_v39_startup_release_order_a01_20261005'
def sha(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def audit():
 freeze=json.loads((PKG/'FREEZE.json').read_text(encoding='utf-8-sig'))
 raw_path=PKG/'results/a03/RAW.json'; raw=json.loads(raw_path.read_text(encoding='utf-8-sig'))
 errors=[]
 head=subprocess.run(['git','-C',str(ROOT),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
 if subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',freeze['base_commit'],head],check=False).returncode!=0:errors.append('freeze_not_ancestor')
 for rel,expected in freeze['source_sha256'].items():
  p=ROOT/rel
  if not p.is_file() or sha(p)!=expected:errors.append('source_hash:'+rel)
 if raw.get('selector_source_verified') is not True:errors.append('selector_source')
 if 'session_map01_v15.py' not in raw.get('selector_source','') or 'session_map01_v12.py' not in raw.get('selector_source',''):errors.append('selector_targets')
 if raw.get('backend_class')!='doom_owner_thread_release_batch_backend_v1.Backend':errors.append('backend_identity')
 if raw.get('owner_class')!='input_transition_owner_v4.InputOwner':errors.append('owner_identity')
 events=raw.get('events',[]); downs=[e for e in events if e.get('event')=='input_admission']; ups=[e for e in events if e.get('event')=='input_release_transition']
 if [e.get('key') for e in downs]!=['F8','SPACE']:errors.append('down_order')
 if [e.get('key') for e in ups]!=['SPACE','F8']:errors.append('up_order')
 if len(ups)!=2 or len(downs)!=2:errors.append('edge_counts')
 for e in downs+ups:
  if e.get('id')!='cover-startup-a01' or e.get('step')!=2:errors.append('program_step_context')
 for e in ups:
  if e.get('grants_input_authority') is not False or e.get('physical_verification_authoritative') is not False:errors.append('authority')
  if e.get('owner_transition_verified') is not True or e.get('release_batch_complete') is not True or e.get('release_batch_size')!=2:errors.append('batch_verification')
  if e.get('owner_thread_keyup_verified') is not True:errors.append('owner_keyup_verified')
  receipt=e.get('owner_thread_keyup_receipt')
  if not isinstance(receipt,dict) or receipt.get('event')!='owner_explicit_keyup' or receipt.get('operation')!='up' or receipt.get('key')!=e.get('key') or receipt.get('server_sync_completed') is not True:errors.append('owner_receipt_contents')
  if e.get('physical_key_measurement') is not None:errors.append('unexpected_physical_measurement_claim')
 ops=raw.get('operations',[]); up_indices=[i for i,x in enumerate(ops) if x.get('op')=='key-up']
 if len(up_indices)!=2:errors.append('raw_up_count')
 else:
  between=ops[up_indices[0]+1:up_indices[1]]
  if between!=raw.get('between_up_operations'):errors.append('between_window_copy')
  if any(x.get('op')=='query_keymap' for x in between):errors.append('query_between')
  if raw.get('keymap_queries_between_ups')!=0:errors.append('query_count')
 if raw.get('fake_physical_after')!=[] or raw.get('backend_held_after')!=[]:errors.append('final_state')
 stop=json.loads((PKG/'results/STOP.json').read_text(encoding='utf-8-sig'))
 if stop.get('status')!='STOP_HARNESS_SOURCE_MISMATCH':errors.append('wrong_harness_stop_retention')
 return {'schema':'map01-v39-startup-release-order-audit-v1','disposition':'PASS_V39_STARTUP_BACKEND_OWNER_FAKE_X_COMPOSITION' if not errors else 'FAIL','errors':errors,'base_commit':head,'freeze_sha256':sha(PKG/'FREEZE.json'),'raw_sha256':sha(raw_path),'raw_operation_count':len(ops),'events':len(events),'keymap_queries_between_ups':raw.get('keymap_queries_between_ups'),'between_up_operations':raw.get('between_up_operations'),'scope':'V39 selector source plus actual V15 telemetry backend, typed-release-v2, release-batch backend, owner-v4 and live_control owner-v12 in deterministic fake-display seam; owner receipts establish XTest/XSync completion, not per-key keymap occupancy; no full session startup or live application'}
if __name__=='__main__':
 result=audit();print(json.dumps(result,sort_keys=True,indent=2));raise SystemExit(bool(result['errors']))
