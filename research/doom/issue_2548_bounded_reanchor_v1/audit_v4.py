from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image

EXPECTED={
 'c01-coast-guard-only':('ADMIT',None),
 'c02-drift-guard-only':('REJECT_CONTEXT_CHANGED','REJECT_NO_FRESH_OBSERVATION'),
 'c03-drift-fresh-reanchor':('REJECT_CONTEXT_CHANGED','ADMIT'),
 'c04-coast-fresh-reanchor':('ADMIT','ADMIT'),
 'c05-stale-receipt-control':('REJECT_CONTEXT_CHANGED','REJECT_PROVENANCE'),
 'c06-cross-session-control':('REJECT_CONTEXT_CHANGED','REJECT_PROVENANCE'),
 'c07-incomplete-receipt-control':('REJECT_CONTEXT_CHANGED','REJECT_PROVENANCE'),
}

def sha256(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def rgb_hash(path):
 with Image.open(path) as im: raw=np.asarray(im.convert('RGB'),dtype=np.uint8).tobytes()
 return hashlib.sha256(raw).hexdigest()

def image_mae(a,b):
 with Image.open(a) as ia, Image.open(b) as ib:
  aa=np.asarray(ia.convert('RGB'),dtype=np.float32);bb=np.asarray(ib.convert('RGB'),dtype=np.float32)
 if aa.shape!=bb.shape:raise ValueError('shape mismatch')
 return float(np.abs(aa-bb).mean()/255.0)

def receipt_verdict(old,fresh,fresh_count):
 required=('session_id','sequence','frame_rgb_sha256','image')
 if any(not old.get(k) or not fresh.get(k) for k in required):return 'REJECT_PROVENANCE','MISSING_RECEIPT_FIELD',None
 if old['session_id']!=fresh['session_id']:return 'REJECT_PROVENANCE','CROSS_SESSION',None
 if fresh['sequence']<=old['sequence'] or f"{old['session_id']}:{old['sequence']}"==f"{fresh['session_id']}:{fresh['sequence']}":return 'REJECT_PROVENANCE','STALE_OR_DUPLICATE_RECEIPT',None
 if fresh_count!=1:return 'REJECT_PROVENANCE','OBSERVATION_BUDGET',None
 a=Path(old['image']);b=Path(fresh['image'])
 if rgb_hash(a)!=old['frame_rgb_sha256'] or rgb_hash(b)!=fresh['frame_rgb_sha256']:return 'REJECT_PROVENANCE','FRAME_HASH_MISMATCH',None
 v=image_mae(a,b)
 return ('ADMIT' if v<=.015 else 'REJECT_CONTEXT_CHANGED'),'FRESH_PAIR_EVALUATED',v

def audit_rows(rows,root,check_files=True):
 errors=[];ids=[r.get('id') for r in rows]
 if len(rows)!=len(EXPECTED):errors.append(f'case_count:{len(rows)} expected:{len(EXPECTED)}')
 if len(set(ids))!=len(ids):errors.append('duplicate_case_ids')
 if set(ids)!=set(EXPECTED):errors.append('case_id_set_mismatch')
 by={r.get('id'):r for r in rows}
 for cid,(guard_expected,reanchor_expected) in EXPECTED.items():
  r=by.get(cid)
  if r is None:continue
  g=r.get('guard_only',{}).get('admission');re=r.get('reanchor',{}).get('admission')
  if g!=guard_expected:errors.append(f'{cid}:guard:{g}:{guard_expected}')
  if reanchor_expected is not None and re!=reanchor_expected:errors.append(f'{cid}:reanchor:{re}:{reanchor_expected}')
  if r.get('terminal_status')!='completed':errors.append(f'{cid}:terminal_not_completed')
  rel=r.get('release') or {}
  if rel.get('verified') is not True or rel.get('keys_down')!=[] or rel.get('buttons_down')!=[]:errors.append(f'{cid}:release_not_verified_empty')
  score=r.get('score') or {}
  if score.get('kill_count')!=0 or score.get('death_count')!=0 or score.get('map_exit') is not False or score.get('player_dead') is not False:errors.append(f'{cid}:unsafe_or_missing_score')
  if not r.get('session_id') or not r.get('runtime_sources_sha256'):errors.append(f'{cid}:missing_session_or_source_identity')
  try:
   observed_guard=image_mae(Path(r['source_receipt']['image']),Path(r['old_receipt']['image']))
   if abs(observed_guard-r['guard_only']['mae'])>1e-12:errors.append(f'{cid}:guard_mae_mismatch')
   if (observed_guard<=.015)!=(g=='ADMIT'):errors.append(f'{cid}:guard_threshold_mismatch')
  except Exception as ex:errors.append(f'{cid}:guard_evidence_error:{type(ex).__name__}:{ex}')
  old=r.get('old_receipt') or {};fresh=r.get('candidate_receipt')
  if reanchor_expected and reanchor_expected!='REJECT_NO_FRESH_OBSERVATION' and fresh is not None:
   calc,reason,v=receipt_verdict(old,fresh,r.get('fresh_observation_count',0))
   if calc!=re or reason!=r.get('reanchor',{}).get('reason'):errors.append(f'{cid}:receipt_recomputation_mismatch')
   if v is not None and abs(v-r.get('reanchor',{}).get('mae',-1))>1e-12:errors.append(f'{cid}:mae_mismatch')
  if cid in ('c03-drift-fresh-reanchor','c04-coast-fresh-reanchor') and r.get('candidate_receipt')!=r.get('captured_fresh_receipt'):errors.append(f'{cid}:candidate_not_captured_fresh_receipt')
  if cid=='c07-incomplete-receipt-control':
   expected_candidate=dict(r.get('captured_fresh_receipt') or {});expected_candidate.pop('frame_rgb_sha256',None)
   if r.get('candidate_receipt')!=expected_candidate:errors.append(f'{cid}:candidate_not_derived_from_captured_receipt')
  if check_files:
   d=root/cid
   try:
    session=json.loads((d/'session.json').read_text());events=[json.loads(x) for x in (d/'capture-events.jsonl').read_text().splitlines() if x.strip()]
    if session.get('session_id')!=r['session_id']:errors.append(f'{cid}:session_receipt_mismatch')
    if session.get('runtime_sources_sha256')!=r['runtime_sources_sha256'] or sha256(d/'runtime'/'sources.json')!=r['runtime_sources_sha256']:errors.append(f'{cid}:runtime_source_hash_mismatch')
    if len(events)!=r.get('event_count'):errors.append(f'{cid}:event_count_mismatch')
    if any(e.get('_capture_session_id')!=r['session_id'] for e in events):errors.append(f'{cid}:event_session_binding_mismatch')
    typed_by_seq={e.get('sequence'):e for e in events if e.get('event')=='typed_observation'}
    images_by_seq={e.get('sequence'):e for e in events if e.get('event')=='observation'}
    measured_fresh=sum(1 for seq in typed_by_seq if seq and seq>r.get('old_receipt',{}).get('sequence',-1))
    if measured_fresh!=r.get('fresh_observation_count'):errors.append(f'{cid}:fresh_observation_count_mismatch')
    for receipt_name in ('source_receipt','old_receipt','captured_fresh_receipt'):
     rec=r.get(receipt_name)
     if rec:
      p=Path(rec['image'])
      if not p.is_file() or rgb_hash(p)!=rec['frame_rgb_sha256']:errors.append(f'{cid}:{receipt_name}_frame_binding_failure')
      if rec:
       event=typed_by_seq.get(rec.get('sequence'));image_event=images_by_seq.get(rec.get('sequence'))
       if not event or not image_event or event.get('frame_rgb_sha256')!=rec.get('frame_rgb_sha256') or image_event.get('image')!=rec.get('image') or event.get('_capture_session_id')!=rec.get('session_id') or image_event.get('_capture_session_id')!=rec.get('session_id'):errors.append(f'{cid}:{receipt_name}_not_in_captured_event_stream')
   except Exception as ex:errors.append(f'{cid}:raw_evidence_error:{type(ex).__name__}:{ex}')
 if 'c05-stale-receipt-control' in by:
  r=by['c05-stale-receipt-control']
  if r.get('candidate_receipt')!=r.get('old_receipt'):errors.append('stale_control_did_not_reuse_old_receipt')
 if 'c06-cross-session-control' in by:
  r=by['c06-cross-session-control'];donor=by.get('c04-coast-fresh-reanchor',{})
  if r.get('candidate_receipt')!=donor.get('captured_fresh_receipt'):errors.append('cross_session_control_not_bound_to_captured_donor')
  elif r.get('candidate_receipt',{}).get('session_id')==r.get('session_id'):errors.append('cross_session_control_session_not_distinct')
 if 'c07-incomplete-receipt-control' in by and by['c07-incomplete-receipt-control'].get('candidate_receipt',{}).get('frame_rgb_sha256') is not None:errors.append('incomplete_receipt_control_field_present')
 return errors

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--results',type=Path,required=True);ap.add_argument('--root',type=Path,required=True);a=ap.parse_args()
 rows=json.loads(a.results.read_text());errors=audit_rows(rows,a.root,True)
 report={'schema':'issue-2548-audit-v4','status':'PASS' if not errors else 'FAIL','case_count':len(rows),'errors':errors,'results_sha256':sha256(a.results)}
 print(json.dumps(report,indent=2,sort_keys=True));raise SystemExit(0 if not errors else 1)
if __name__=='__main__':main()
