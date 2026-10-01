import json
from pathlib import Path
FAMILIES={
'SUCCEEDED':('ok',False,False),
'IN_PROGRESS':('working',False,False),
'BLOCKED':('error',True,False),
'AUTHORITY_REQUIRED':('error',False,False),
'TARGET_NOT_FOUND':('error',False,False),
'CAPABILITY_UNSUPPORTED':('error',False,False),
'CONFLICT':('error',False,False),
'IMPOSSIBLE_UNDER_CONSTRAINTS':('error',True,False),
'FAILED_UNKNOWN':('error',False,True),
}
rows=[]
for family,(status,timeout,contradictory) in FAMILIES.items():
  retries=['IDENTICAL_RETRY_VALID','REQUIRES_CHANGE'] if family=='BLOCKED' else ['REQUIRES_CHANGE']
  for freshness in ['CURRENT','STALE']:
    for completeness in ['COMPLETE','INCOMPLETE']:
      for retry_context in retries:
        for rep in range(2):
          rows.append({'row_id':len(rows),'family':family,'freshness':freshness,'completeness':completeness,
            'retry_context':retry_context,'status':status,'timeout':timeout,'contradictory':contradictory,'rep':rep})
Path(__file__).with_name('corpus.json').write_text(json.dumps(rows,sort_keys=True,indent=2)+'\n')
print(len(rows))
