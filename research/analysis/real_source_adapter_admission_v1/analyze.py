import json,pathlib
root=pathlib.Path(__file__).parent
f=json.loads((root/'fixture.json').read_text())

def candidate(row):
    if row['source']=='focus_generation_identity':
        return row['generation_delta']==0 and not row['identity_changed']
    if row['source']=='chromium_coarse_context':
        return row['context_equal']
    raise ValueError(row['source'])

stats={}
for src in sorted({r['source'] for r in f['rows']}):
    rows=[r for r in f['rows'] if r['source']==src]
    fa=sum(candidate(r) and not r['oracle_admit'] for r in rows)
    fr=sum((not candidate(r)) and r['oracle_admit'] for r in rows)
    stats[src]={
      'rows':len(rows),
      'false_accepts':fa,
      'false_rejects':fr,
      'evidence_complete':'ADMISSIBLE' if fa==0 and fr==0 else 'INCOMPLETE',
      'name_only':'ADMISSIBLE'
    }
result={
 'pinned':f['pinned'],
 'rows':len(f['rows']),
 'stats':stats,
 'name_only_false_complete':int(stats['chromium_coarse_context']['name_only']=='ADMISSIBLE' and stats['chromium_coarse_context']['false_accepts']>0)
}
pass_gate=(stats['focus_generation_identity']['evidence_complete']=='ADMISSIBLE' and
           stats['focus_generation_identity']['false_accepts']==0 and
           stats['focus_generation_identity']['false_rejects']==0 and
           stats['chromium_coarse_context']['evidence_complete']=='INCOMPLETE' and
           stats['chromium_coarse_context']['false_accepts']>0 and
           result['name_only_false_complete']>0)
result['decision']='PASS_REAL_SOURCE_ADAPTER_ADMISSION_SCOPED' if pass_gate else 'FAIL_REAL_SOURCE_ADAPTER_ADMISSION'
print(json.dumps(result,indent=2,sort_keys=True))
