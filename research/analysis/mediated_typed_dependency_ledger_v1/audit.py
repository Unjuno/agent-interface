import argparse,json,pathlib

def audit(root):
 root=pathlib.Path(root);cs=json.loads((root/'CASES.json').read_text());raw=json.loads((root/'RAW_LEDGER.json').read_text());res=json.loads((root/'RESULT.json').read_text())
 counts={'branch_states':0,'alias_states':0,'query_states':0,'ledger_mismatch':0,'unsafe_acceptances':0,'false_invalidations':0,'malformed_receipts':0}
 for z in cs:
  k=z['kind'];st=z['state'];led=raw[z['id']]['ledger']
  if k=='branch':
   counts['branch_states']+=1;g=st['values']['g'];exp=[{'type':'READ','resource':'g','version':1},{'type':'READ','resource':'a' if g else 'b','version':1}];deps={'g','a' if g else 'b'};muts=('g','a','b','u')
   def inv(m):return any(x['type']=='READ' and x['resource']==m for x in led)
  elif k=='alias':
   counts['alias_states']+=1;t=st['target'];exp=[{'type':'RESOLVE','alias':'slot','mapping_version':1,'identity':t},{'type':'READ','resource':t,'version':1}];deps={'mapping',t};muts=('mapping','A','B','u')
   def inv(m):return (m=='mapping' and any(x['type']=='RESOLVE' for x in led)) or any(x['type']=='READ' and x['resource']==m for x in led)
  elif k=='query':
   counts['query_states']+=1;ms=st['members'];exp=[{'type':'QUERY','scope':'S','membership_version':1}]+[{'type':'READ','resource':'value_'+m,'version':1} for m in ms];deps={'query'}|{'value_'+m for m in ms};muts=('query','value_A','value_B','u')
   def inv(m):return (m=='query' and any(x['type']=='QUERY' for x in led)) or any(x['type']=='READ' and x['resource']==m for x in led)
  else:
   counts['malformed_receipts']=len(led);continue
  counts['ledger_mismatch']+=int(led!=exp)
  for m in muts:
   required=m in deps;invalid=inv(m)
   counts['unsafe_acceptances']+=int(required and not invalid);counts['false_invalidations']+=int((not required) and invalid)
 schedule=json.loads((root/'TASK_SCHEDULE.json').read_text())
 checks={
  'case_count':res['case_count']==65 and res['scientific_case_count']==64,
  'families':counts['branch_states']==16 and counts['alias_states']==16 and counts['query_states']==32,
  'ledger_exact':counts['ledger_mismatch']==0,
  'validation_safe':counts['unsafe_acceptances']==0,
  'validation_minimal':counts['false_invalidations']==0,
  'malformed_fail_closed':counts['malformed_receipts']==0,
  'task_schedule_only_id_kind':all(set(x)=={'id','kind'} for x in schedule) and res['client_schedule_fields']==['id','kind'],
  'budget':res['formal_invocations']==1 and res['reruns']==0 and res['replacements']==0 and res['tuning']==0
 }
 out={'counts':counts,'checks':checks,'decision':'PASS_MEDIATED_TYPED_DEPENDENCY_LEDGER_SCOPED' if all(checks.values()) else 'FAIL_MEDIATED_TYPED_DEPENDENCY_LEDGER','pass':all(checks.values())}
 (root/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True));print(json.dumps(out,indent=2,sort_keys=True));raise SystemExit(0 if out['pass'] else 1)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root');audit(p.parse_args().root)
