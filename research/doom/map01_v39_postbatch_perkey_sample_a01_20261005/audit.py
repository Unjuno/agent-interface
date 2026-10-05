#!/usr/bin/env python3
"""Independent raw-only audit of the post-batch per-key keymap prototype."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def check_case(case):
 events=case['events']; ops=case['operations']; rows=[x for x in events if x.get('event')=='input_release_transition']
 ups=[x for x in ops if x.get('event')=='key_up']; downs=[x for x in ops if x.get('event')=='key_down']
 between=[]
 if len(ups)==2:
  ordered=sorted(ops,key=lambda x:x['time_ns']); positions=[i for i,x in enumerate(ordered) if x.get('event')=='key_up']
  between=ordered[positions[0]+1:positions[1]]
  assert sum(x.get('event')=='query_keymap' for x in between)==0
  assert [x['keycode'] for x in ups]==[38,65]
 else: raise AssertionError('expected two key-up edges')
 if case['scenario']=='sample_error':
  assert case['candidate_exception'] and 'injected keymap sample failure' in case['candidate_exception']
  assert all('post_batch_key_state_sample' not in x for x in rows)
  assert all(x.get('release_batch_complete') is False for x in rows)
  assert any(x.get('event')=='query_keymap_error' for x in ops)
  assert case['sample_returned'] is False
  return {'scenario':'sample_error','disposition':'UNKNOWN_FAIL_CLOSED_NO_PER_KEY_CONFIRMATION','rows':len(rows)}
 assert case['candidate_exception'] is None
 sample=case.get('sample_returned')
 assert sample is True
 post=[x for x in ops if x.get('event')=='postbatch_keymap_sample']
 assert len(post)==1
 sample_event=post[0]
 last_up=max(x['time_ns'] for x in ups)
 assert last_up<=sample_event['sample_started_ns']<=sample_event['sample_finished_ns']
 assert len(rows)==2 and [x.get('key') for x in rows]==['a','space']
 admissions=[x for x in events if x.get('event')=='input_admission']
 for row in rows:
  matches=[x for x in admissions if all(x.get(k)==row.get(k) for k in ('key','id','step','owner_id','intent_token'))]
  assert len(matches)==1,'release row lacks unique admission identity'
  receipt=row.get('owner_thread_keyup_receipt'); measure=row.get('post_batch_key_state_sample')
  assert isinstance(receipt,dict) and receipt.get('server_sync_completed') is True
  assert isinstance(measure,dict)
  assert measure.get('keycode')==receipt.get('keycode')
  assert measure.get('owner_id')==row.get('owner_id')==receipt.get('owner_id')
  assert measure.get('intent_token')==row.get('intent_token')==receipt.get('intent_token')
  assert measure.get('program_id')==row.get('id') and measure.get('step')==row.get('step')
  assert measure.get('sample_started_ns')==sample_event.get('sample_started_ns')
  assert measure.get('sample_finished_ns')==sample_event.get('sample_finished_ns')
  assert measure.get('physical_verification_authoritative') is False
  assert measure.get('application_consumption_observed') is False
 if case['scenario']=='normal':
  assert sample_event['sampled_owned_keycodes_down']==[]
  assert all(x['post_batch_key_state_sample']['status']=='KEY_UP_AT_POSTBATCH_SAMPLE' for x in rows)
  return {'scenario':'normal','disposition':'PASS_TWO_PER_KEY_RESULTS_AT_SHARED_POSTBATCH_SAMPLE','rows':2}
 if case['scenario']=='release_stuck':
  assert sample_event['sampled_owned_keycodes_down']==[65]
  statuses={x['key']:x['post_batch_key_state_sample']['status'] for x in rows}
  assert statuses=={'a':'KEY_UP_AT_POSTBATCH_SAMPLE','space':'PHYSICAL_STILL_DOWN_AT_POSTBATCH_SAMPLE'}
  assert case['physical_keycodes_before_close']==[65]
  return {'scenario':'release_stuck','disposition':'PASS_RESIDUAL_KEY_IDENTIFIED','rows':2}
 raise AssertionError('unknown scenario')
def main():
 freeze=json.loads((HERE/'FREEZE.json').read_text())
 for rel,digest in freeze['source_sha256'].items():
  assert sha((ROOT/rel).read_bytes())==digest,'source hash mismatch '+rel
 candidate=HERE/'run_candidate.py'; assert sha(candidate.read_bytes())==freeze['candidate_sha256'],'candidate hash mismatch'
 raw_bytes=(HERE/'results/a01/raw.json').read_bytes(); raw=json.loads(raw_bytes)
 assert raw['run_id']==freeze['run_id'] and raw['base_commit']==freeze['base_commit']
 assert [x['scenario'] for x in raw['scenarios']]==freeze['scenarios']
 outcomes=[check_case(x) for x in raw['scenarios']]
 audit={'schema':'map01-v39-postbatch-perkey-sample-audit-v1','run_id':freeze['run_id'],
        'status':'PASS_METHOD_SCOPED_POSTBATCH_SAMPLE_AND_FAIL_CLOSED_CONTROLS',
        'base_commit':freeze['base_commit'],'raw_sha256':sha(raw_bytes),'scenarios':outcomes,
        'inter_release_keymap_queries':0,'authority_granted':False,'application_consumption_observed':False,
        'scope':raw['scope']}
 out=HERE/'results/a01/AUDIT.json';out.write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
 print(json.dumps({'status':audit['status'],'scenarios':outcomes,'audit_sha256':sha(out.read_bytes())},sort_keys=True))
 return 0
if __name__=='__main__':
 try: raise SystemExit(main())
 except Exception as exc: print(type(exc).__name__+': '+str(exc),file=sys.stderr); raise
