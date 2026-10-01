import json,sys,pathlib,hashlib
DEPS=['form_generation','required_form_generation','intent_version','producer_version','source_generation','source_current','intent']

def truth(state):
    if type(state.get('source_current')) is not bool:
        raise ValueError('bad source_current')
    ints=['form_generation','required_form_generation','intent_version','producer_version','source_generation']
    if any(type(state.get(k)) is not int or state[k] < 0 for k in ints):
        raise ValueError('bad generation')
    if state.get('intent') not in {'submit','inspect'}: raise ValueError('bad intent')
    if not state['source_current']: return 'UNKNOWN'
    return 'TRUE' if state['form_generation']==state['required_form_generation'] and state['intent']=='submit' else 'FALSE'

def dep_key(s): return {k:s[k] for k in DEPS}

def audit_data(data):
    errs=[]; seen=set(); naive_wrong=naive_unsafe=naive_stale=0; cand_wrong=cand_stale=cand_hits=naive_hits=0
    expected_cases={'SAME','IRRELEVANT_CHANGE','FORM_DEP_CHANGE','SEMANTIC_ABA_NEW_GENERATION','INTENT_CHANGE','PRODUCER_CHANGE','SOURCE_REPLACED','SOURCE_STALE'}
    counts={}
    if data.get('schema')!='predicate-persist-formal-v1' or data.get('formal_invocations')!=1: errs.append('header')
    for r in data.get('rows',[]):
      ident=(r.get('rep'),r.get('case'),r.get('policy'))
      if ident in seen: errs.append('duplicate_row')
      seen.add(ident); counts[ident]=counts.get(ident,0)+1
      try: oracle=truth(r['after']); same=dep_key(r['before'])==dep_key(r['after'])
      except Exception: errs.append('state_schema'); continue
      res=r.get('result',{})
      if r.get('case') not in expected_cases or r.get('rep') not in {0,1,2}: errs.append('schedule')
      if r.get('prepare_exit')!=0 or r.get('consume_exit')!=0 or r.get('prepare_stderr') or r.get('consume_stderr'): errs.append('exit_or_stderr')
      if res.get('oracle')!=oracle or res.get('correct')!=(res.get('value')==oracle): errs.append('result_oracle_mismatch')
      if res.get('executable') != (res.get('value')=='TRUE' and r['after']['source_current']): errs.append('exec_flag')
      if r.get('policy')=='VALUE_ONLY_PERSIST':
        naive_hits += int(res.get('reused') is True)
        naive_wrong += int(res.get('value') != oracle)
        naive_unsafe += int(res.get('executable') is True and oracle!='TRUE')
        naive_stale += int(res.get('reused') is True and not same)
      elif r.get('policy')=='DEPENDENCY_BOUND_PERSIST':
        cand_hits += int(res.get('reused') is True)
        cand_wrong += int(res.get('value') != oracle)
        cand_stale += int(res.get('reused') is True and not same)
        if same and res.get('reused') is not True: errs.append('candidate_missed_exact_key')
        if (not same) and res.get('reused') is True: errs.append('candidate_stale_hit')
      else: errs.append('policy')
    if len(data.get('rows',[]))!=48 or len(seen)!=48: errs.append('row_denominator')
    for rep in range(3):
      for case in expected_cases:
        for policy in ['VALUE_ONLY_PERSIST','DEPENDENCY_BOUND_PERSIST']:
          if counts.get((rep,case,policy))!=1: errs.append('missing_schedule_cell')
    controls=data.get('controls',[])
    if {c.get('name') for c in controls}!={'BOOL_VERSION','BAD_DIGEST','MISSING_KEY','WRONG_SCHEMA'}: errs.append('controls_set')
    for c in controls:
      if c.get('exit')!=0 or c.get('stderr') or c.get('result',{}).get('reused') is True: errs.append('control_'+str(c.get('name')))
      try:
        oracle=truth(c['state'])
        if c['result'].get('value')!=oracle: errs.append('control_value_'+str(c.get('name')))
      except Exception: errs.append('control_state')
    summary={'errors':sorted(set(errs)),'row_count':len(data.get('rows',[])),'naive_wrong_rows':naive_wrong,'naive_unsafe_exec_rows':naive_unsafe,'naive_stale_provenance_reuse_rows':naive_stale,'candidate_wrong_rows':cand_wrong,'candidate_stale_hits':cand_stale,'candidate_hits':cand_hits,'naive_hits':naive_hits,'controls':len(controls)}
    summary['pass_contract']=(not summary['errors'] and summary['row_count']==48 and naive_wrong==9 and naive_unsafe==6 and naive_stale==18 and cand_wrong==0 and cand_stale==0 and cand_hits==6 and naive_hits==48 and len(controls)==4)
    return summary

def main():
  root=pathlib.Path(__file__).parent; data=json.loads((root/'FORMAL.json').read_text()); s=audit_data(data)
  (root/'AUDIT.json').write_text(json.dumps(s,sort_keys=True,indent=2)+'\n'); print(json.dumps(s,sort_keys=True)); sys.exit(0 if s['pass_contract'] else 1)
if __name__=='__main__': main()
