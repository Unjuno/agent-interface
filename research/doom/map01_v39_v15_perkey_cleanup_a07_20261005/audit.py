#!/usr/bin/env python3
"""Independent raw/source audit for current-main V39/V15 cleanup A05."""
from __future__ import annotations
import hashlib, json, pathlib, sys
PACKAGE = pathlib.Path(__file__).resolve().parent
freeze = json.loads((PACKAGE/'FREEZE.json').read_text(encoding='utf-8'))
manifest = json.loads((PACKAGE/'source-manifest.json').read_text(encoding='utf-8'))
if len(sys.argv) != 3: raise SystemExit('usage: audit.py RAW_PATH AUDIT_OUTPUT_PATH')
raw_path = pathlib.Path(sys.argv[1]).resolve()
out_path = pathlib.Path(sys.argv[2]).resolve()
raw = json.loads(raw_path.read_text(encoding='utf-8'))
checks=[]
def check(name, condition, detail=''):
    checks.append({'name':name,'pass':bool(condition),'detail':str(detail)})
check('raw_schema', raw.get('schema') == 'v39-v15-keyup-loss-a07-raw-v1', raw.get('schema'))
check('source_commit', raw.get('source_base') == manifest['source_commit'], raw.get('source_base'))
check('claims_are_limited', all(v is False for v in raw.get('claims',{}).values()) and
      set(raw.get('claims',{})) == {'real_x11','gui','doom','model','physical_keyboard','application_effect'}, raw.get('claims'))
cases=raw.get('cases',[])
check('paired_cases',len(cases)==2,len(cases))
by_loss={c.get('injected_keyrelease_loss'):c for c in cases}
check('both_arms_present',set(by_loss)=={False,True},list(by_loss))
for label,loss in [('normal',False),('injected_loss',True)]:
    case=by_loss.get(loss,{})
    row=case.get('release_row') or {}
    terminal=case.get('executor_terminal') or {}
    release=terminal.get('release') or {}
    check(label+'_executor_completed',terminal.get('status')=='completed',terminal.get('status'))
    check(label+'_fixture_operation_observed',any(e.get('event')=='step_started' and e.get('operation')=='fixture_actions' for e in case.get('events',[])),[e.get('operation') for e in case.get('events',[]) if e.get('event')=='step_started'])
    check(label+'_server_neutral_after_executor',case.get('server_keycodes_down_after_executor_release')==[],case.get('server_keycodes_down_after_executor_release'))
    check(label+'_single_release_row',row.get('event')=='input_release_transition' and
          sum(1 for e in case.get('events',[]) if e.get('event')=='input_release_transition')==1,
          row.get('event'))
    check(label+'_owner_transition_verified',row.get('owner_transition_verified') is True,row.get('owner_transition_verified'))
    check(label+'_no_physical_authority',row.get('physical_verification_authoritative') is False,row.get('physical_verification_authoritative'))
    check(label+'_terminal_verified',release.get('verified') is True,release.get('verified'))
    check(label+'_close_recovered',case.get('owner_close_recovered') is True and case.get('owner_close_error') is None,
          case.get('owner_close_error'))
    receipt=row.get('owner_thread_keyup_receipt') or {}
    attempts=receipt.get('server_keyup_attempts') or []
    check(label+'_attempt_count_matches',receipt.get('server_keyup_attempt_count')==len(attempts),len(attempts))
    check(label+'_attempt_clock_order',all(
        type(a.get('keyrelease_started_ns')) is int and type(a.get('sync_returned_ns')) is int and
        type(a.get('keymap_sampled_ns')) is int and
        a['keyrelease_started_ns']<=a['sync_returned_ns']<=a['keymap_sampled_ns']
        for a in attempts),len(attempts))
    check(label+'_attempt_chain_contiguous',all(
        prev['keymap_sampled_ns']<=cur['keyrelease_started_ns'] and
        prev.get('server_key_down_after') is cur.get('server_key_down_before')
        for prev,cur in zip(attempts,attempts[1:])),len(attempts))
    if loss:
        check('loss_retry_detected_then_cleared',len(attempts)==2 and
              attempts[0].get('server_key_down_after') is True and
              attempts[1].get('server_key_down_after') is False,
              [a.get('server_key_down_after') for a in attempts])
    else:
        check('normal_single_attempt',len(attempts)==1 and attempts[0].get('server_key_down_after') is False,
              [a.get('server_key_down_after') for a in attempts])
# Independently verify each retained source snapshot and materialized source byte sequence.
source_results={}
for rel,pin in manifest['files'].items():
    materialized=PACKAGE/pin['path']
    actual=materialized.read_bytes() if materialized.is_file() else b''
    data=actual
    source_results[rel]={'source_sha256':hashlib.sha256(data).hexdigest(),
                         'expected_sha256':pin['sha256'],
                         'materialized_sha256':hashlib.sha256(actual).hexdigest(),
                         'pass':len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256'] and actual==data}
check('all_21_materialized_sources_match',len(source_results)==21 and all(x['pass'] for x in source_results.values()),
      [p for p,x in source_results.items() if not x['pass']])
candidate=PACKAGE/'candidate.py'
candidate_sha=hashlib.sha256(candidate.read_bytes()).hexdigest()
check('candidate_hash_matches_freeze',candidate_sha==freeze['candidate_sha256'],candidate_sha)
source_manifest_sha=hashlib.sha256((PACKAGE/'source-manifest.json').read_bytes()).hexdigest()
check('source_manifest_hash_matches_freeze',source_manifest_sha==freeze['source_manifest_sha256'],source_manifest_sha)
passed=all(x['pass'] for x in checks)
loss_case=by_loss.get(True,{})
loss_terminal=loss_case.get('executor_terminal') or {}
loss_down=loss_case.get('server_keycodes_down_after_executor_release')
decision=('PASS_SINGLE_DROPPED_KEYRELEASE_RECOVERED_BEFORE_TERMINAL'
          if passed and loss_terminal.get('status')=='completed' and loss_down==[] else
          'FAIL_TERMINAL_RELEASE_NOT_VERIFIED' if passed else 'AUDIT_FAILURE')
out={'schema':'v39-v15-perkey-cleanup-a07-audit-v1',
     'status':'PASS_RAW_AND_SOURCE_AUDIT' if passed else 'FAIL_RAW_OR_SOURCE_AUDIT',
     'scientific_disposition':decision,
     'passed':sum(x['pass'] for x in checks),'total':len(checks),
     'checks':checks,'source_results':source_results,
     'raw_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
     'live_or_physical_release_claim':False}
out_path.parent.mkdir(parents=True,exist_ok=True)
out_path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'status':out['status'],'decision':decision,'passed':out['passed'],'total':out['total']}))
if not passed: raise SystemExit(1)
