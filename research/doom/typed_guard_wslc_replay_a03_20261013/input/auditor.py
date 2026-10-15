import hashlib, json, sys
from pathlib import Path
report_path, events_path, candidate_path, audit_path = map(Path,sys.argv[1:5])
report=json.loads(report_path.read_text(encoding='utf-8')); candidate=json.loads(candidate_path.read_text(encoding='utf-8'))
rows=[json.loads(x) for x in events_path.read_text(encoding='utf-8').splitlines() if x.strip()]
typed={e['sequence']:e for e in rows if e.get('event')=='typed_observation'}
artifact={e['sequence']:e for e in rows if e.get('event')=='observation'}
checks=[]; soft=[]; invalid=[]
for d in report['decisions']:
 for e in (d.get('cover_validity_latest_soft_event'),d.get('policy_invalidation')):
  if not e: continue
  seq=e['sequence']; exp=e['outcome']; sid=e.get('signal',{}).get('signal_id') or exp.get('signal_id') or e.get('reason','').split(':',1)[0]
  adm=d['cover_validity_admission']; source=adm.get('source_ammo_signal') if sid=='ammo' else adm.get('source_signal'); current=typed[seq]['signals'][sid]
  recorded=e.get('signal') or e.get('signals',{}).get(sid)
  assert recorded is not None and all(current.get(k)==recorded.get(k) for k in ('format','status','signal_id','value','sequence','capture_ns','binding','wad_sha256'))
  age=(current['capture_ns']-source['capture_ns'])/1e6
  if current.get('status')!='observed' or current.get('signal_id')!=sid: status,reason='UNKNOWN','signal_unavailable'
  elif current.get('binding')!=source.get('binding'): status,reason='UNKNOWN','binding_changed'
  elif type(current.get('sequence')) is not int or current['sequence']<=source['sequence']: status,reason='UNKNOWN','nonadvancing_sequence'
  elif type(current.get('capture_ns')) is not int or current['capture_ns']<=source['capture_ns']: status,reason='UNKNOWN','invalid_sample_time'
  elif age>adm['effective']['max_source_age_ms']: status,reason='UNKNOWN','source_expired'
  elif type(current.get('value')) is not int or not 0<=current['value']<=1000000: status,reason='UNKNOWN','invalid_signal_value'
  elif current['value']<exp['hard_minimum']: status,reason='HARD_INVALIDATED','below_hard_minimum'
  elif current['value']!=source['value']: status,reason='SOFT_CHANGED','within_validity_envelope'
  else: status,reason='UNCHANGED','signal_unchanged'
  assert status==exp['status'] and reason==exp['reason'],(seq,status,reason,exp['status'],exp['reason'])
  row=next((x for x in candidate['events'] if x['sequence']==seq and x['signal_id']==sid),None); assert row is not None
  assert row['status']==status and row['typed_matches_report'] is True and row['input_authority'] is False
  assert row['returned_invalidation']==(status not in ('SOFT_CHANGED','UNCHANGED'))
  assert row['artifact_ready_minus_typed_emit_ms']==round((artifact[seq]['artifact_ready_ns']-typed[seq]['emit_ns'])/1e6,3)
  assert exp['grants_input_authority'] is False and exp['may_only_preserve_or_reduce_existing_authority'] is True
  if status=='SOFT_CHANGED': soft.append(seq)
  if status in ('UNKNOWN','HARD_INVALIDATED'): invalid.append(seq)
  checks.append({'sequence':seq,'signal_id':sid,'status':status,'age_ms':round(age,6),'independently_reconstructed':True})
assert candidate['candidate_semantic_match'] is True and candidate['input_authority_granted'] is False
assert len(checks)==4 and soft==[96,160] and invalid==[99,170]
out={'schema':'wslc-typed-policy-replay-independent-audit-v1','checks':checks,'soft_event_rows':soft,'invalidation_sequences':invalid,'candidate_rows_independently_reconstructed':True,'authority_never_granted':True,'reported_cumulative_soft_count':report['cover_validity_soft_events'],'selected_soft_rows':len(soft),'limitation':'The retained report exposes selected latest soft rows, not every row behind its cumulative soft count.'}
audit_path.parent.mkdir(parents=True,exist_ok=True); audit_path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,sort_keys=True))
