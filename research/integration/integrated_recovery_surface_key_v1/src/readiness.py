import hashlib,json,sys
from pathlib import Path
EXPECTED={
 '855':'46f08082f3bd58ed67b9a8a16d3fe26c10774d6d7ead246202a10c40e724e9ae',
 '864':'5c7725f878028e620a4edf975fe890b0b2d8fda0071cd286a3c70163ca4d96d6',
}

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main(root,out):
 root=Path(root); rows=[]; errors=[]
 for cohort in ('855','864'):
  arc=root/'predecessor'/cohort/'evidence.tar.xz'
  got=sha(arc)
  if got!=EXPECTED[cohort]: errors.append(f'{cohort}:archive_sha')
  cases=sorted((root/'predecessor'/cohort/'cases').glob('*/case.json'))
  if len(cases)!=8: errors.append(f'{cohort}:case_count')
  for p in cases:
   d=json.loads(p.read_text()); s=d['source']; c=d['admission']
   row={
    'cohort':cohort,'case_id':d['case_id'],'case_sha256':sha(p),
    'source_client_id_present':type(s.get('client_id')) is int,
    'current_client_id_present':type(c.get('client_id')) is int,
    'source_transient_field_present':'transient_for' in s,
    'current_transient_field_present':'transient_for' in c,
    'source_surface_label':s.get('surface',s.get('surface_kind')),
    'current_surface_label':c.get('surface',c.get('surface_kind')),
   }
   rows.append(row)
 summary={
  'task':'INTEGRATED-RECOVERY-SURFACE-KEY-20260917-001',
  'formal_rows_executed':0,'formal_invocations':0,
  'archive_sha_exact':not errors,
  'cases':len(rows),
  'client_id_complete_855':all(r['source_client_id_present'] and r['current_client_id_present'] for r in rows if r['cohort']=='855'),
  'client_id_complete_864':all(r['source_client_id_present'] and r['current_client_id_present'] for r in rows if r['cohort']=='864'),
  'transient_relation_complete_855':all(r['source_transient_field_present'] and r['current_transient_field_present'] for r in rows if r['cohort']=='855'),
  'transient_relation_complete_864':all(r['source_transient_field_present'] and r['current_transient_field_present'] for r in rows if r['cohort']=='864'),
  'decision':None,'errors':errors,'rows':rows,
 }
 summary['decision']='HOLD_PREDECESSOR_IDENTITY_INCOMPLETE' if (summary['client_id_complete_855'] and not summary['transient_relation_complete_855'] and summary['transient_relation_complete_864'] and not errors) else 'FAIL_UNEXPECTED_READINESS_STATE'
 Path(out).write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
 print(json.dumps({k:summary[k] for k in summary if k!='rows'},sort_keys=True))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
