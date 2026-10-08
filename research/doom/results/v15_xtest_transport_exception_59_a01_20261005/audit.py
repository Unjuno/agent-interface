import hashlib, json
from pathlib import Path
root=Path(__file__).resolve().parent
freeze=json.loads((root/'FREEZE.json').read_text(encoding='utf-8-sig'))
raw=json.loads((root/'RAW.json').read_text(encoding='utf-8-sig'))
checks=[]
for rel, info in freeze['sources'].items():
    path=root/'frozen_source'/Path(rel).name
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    checks.append((f'source:{rel}', digest==info['sha256']))
checks.append(('two fault cases', {x['mode'] for x in raw}=={'send','sync'}))
for row in raw:
    checks.extend([
        (f"{row['mode']}: raised injected OSError", row['up_batch_outcome'].startswith('OSError: synthetic ')),
        (f"{row['mode']}: only first ordered UP attempted", len(row['initial_keyrelease_codes'])==1 and row['initial_keyrelease_codes']==[39]),
        (f"{row['mode']}: no explicit receipt before cleanup", row['explicit_receipts_before_cleanup']==0),
        (f"{row['mode']}: separate cleanup succeeded", row['cleanup_verified'] is True and row['remaining_keys']==[] and row['owner_release_records']==1),
        (f"{row['mode']}: owner thread not marked failed", row['owner_failed'] is False),
    ])
report={'schema':'v15-xtest-transport-audit-v1','checks':[{'name':n,'pass':bool(ok)} for n,ok in checks], 'pass':all(ok for _,ok in checks)}
(root/'AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'checks':len(checks),'pass':report['pass']}))
if not report['pass']: raise SystemExit(1)
