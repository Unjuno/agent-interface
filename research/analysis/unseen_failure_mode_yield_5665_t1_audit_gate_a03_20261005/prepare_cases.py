import hashlib, json, pathlib
base_path=pathlib.Path('/src/base.jsonl')
out=pathlib.Path('/cases')
raw=base_path.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='f497948e2d45e793b612b43265ef5b12d81479695a7b27cf7ba733e3d12573f2'
lines=raw.splitlines(keepends=True)
rows=[json.loads(line) for line in lines if line.strip()]
assert len(rows)==204 and sum(r.get('kind')=='iid' for r in rows)==200
seed=5665002
idx=next(i for i,r in enumerate(rows) if r.get('kind')=='iid' and r.get('seed')==seed)
assert rows[idx]['case_id']=='iid-001'

def eligible(r):
    return (r.get('kind')=='iid'
      and r.get('train_planned_n')==len(r.get('train',[]))+r.get('train_unknown_n',0) and r.get('train_unknown_n')==0
      and r.get('validation_planned_n')==len(r.get('validation',[]))+r.get('validation_unknown_n',0) and r.get('validation_unknown_n')==0
      and len(r.get('train_unit_ids',[]))==len(r.get('train',[])) and len(set(r.get('train_unit_ids',[])))==len(r.get('train_unit_ids',[]))
      and len(r.get('validation_unit_ids',[]))==len(r.get('validation',[])) and len(set(r.get('validation_unit_ids',[])))==len(r.get('validation_unit_ids',[]))
      and r.get('train_taxonomy')==r.get('validation_taxonomy') and r.get('train_stratum')==r.get('validation_stratum'))
assert sum(eligible(r) for r in rows)==200
cases={'base':None,'nonexchangeable':('validation_stratum','mutation-shifted-validation-stratum','HOLD_NONEXCHANGEABLE'),'denominator':('validation_unknown_n',None,'HOLD_NO_ELIGIBLE_DENOMINATOR'),'taxonomy':('validation_taxonomy','failure-taxonomy-v2','HOLD_TAXONOMY_UNSTABLE'),'duplicate-unit':('validation_unit_ids',None,'HOLD_NONEXCHANGEABLE')}
summary={}
for name,mutation in cases.items():
    if name=='base': changed=raw
    else:
        changed_row=dict(rows[idx]); changed_row['candidate']=dict(changed_row['candidate'])
        field,value,disposition=mutation
        if name=='denominator': changed_row[field]=changed_row[field]+1
        elif name=='duplicate-unit':
            ids=list(changed_row[field]); ids[-1]=ids[0]; changed_row[field]=ids
        else: changed_row[field]=value
        changed_row['candidate']['disposition']=disposition
        newline=json.dumps(changed_row,separators=(',',':'),ensure_ascii=False).encode('utf-8')+(b'\n' if lines[idx].endswith(b'\n') else b'')
        altered=list(lines); altered[idx]=newline; changed=b''.join(altered)
        parsed=[json.loads(line) for line in changed.splitlines() if line.strip()]
        diffs=[n for n,(a,b) in enumerate(zip(rows,parsed)) if a!=b]
        assert diffs==[idx] and len(parsed)==204
        assert sum(eligible(r) for r in parsed)==199
    path=out/f'{name}.jsonl'; path.write_bytes(changed)
    summary[name]={'sha256':hashlib.sha256(changed).hexdigest(),'bytes':len(changed),'rows':204,'eligible_iid':sum(eligible(json.loads(line)) for line in changed.splitlines() if line.strip())}
(out/'PREPARED.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PREFLIGHT_CASES_PREPARED','target_audit_invocations':0,'cases':summary},sort_keys=True))

