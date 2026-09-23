import hashlib,json
from pathlib import Path
from openpyxl import load_workbook
p=Path(__file__).resolve().parent
summary={'runs':[],'matched_benefit_established':False}
links=0
for i in (1,2):
    run=p/f'run-{i}'; load=lambda name:json.loads((run/name).read_text())
    wb=load_workbook(run/'sheet.xlsx',read_only=True,data_only=False)
    actual=[wb.active[c].value for c in ('A1','A2','B1')]; wb.close()
    assert actual==([762,None,745] if i==1 else [551,768,None])
    assert load('evaluation.json')['success'] is (i==2)
    assert load('evaluation.json')['actual']==actual[:2]
    goal=load('goal.json')
    if i==1: assert 'task' not in goal
    else: assert goal['task']=={'kind':'write_cells','cells':{'A1':551,'A2':768},'save_format':'xlsx'}
    actions=load('actions.json')
    assert [a['interaction'] for a in actions]==['keyboard','click']
    assert all(a['result']['status']=='completed' for a in actions)
    assert all(r['verified'] and r['keys_down']==r['buttons_down']==[]
               for a in actions for r in a['result']['execution']['releases'])
    assert all('visual_watch' not in a for a in actions)
    programs=[json.loads(q.read_text()) for q in (run/'bridge').glob('program-*.json')]
    assert len(programs)==2
    assert sum(not any(op['op'].startswith('pointer_') for op in pr['ops']) for pr in programs)==1
    for stage in (1,2,3):
        request=run/f'request-{stage}.json'
        assert hashlib.sha256(request.read_bytes()).hexdigest()==load(f'reply-{stage}.json')['decision_sha256']
        assert load(f'request-{stage}.json')['source_sequence']==load(f'source-{stage}.json')['sequence']
    assert load('reply-3.json')['status']=='finished'
    assert all(r['returncode'] is not None for r in load('cleanup.json'))
    def images(v):
        global links
        if isinstance(v,dict):
            n=v.get('native')
            if isinstance(n,dict) and 'artifact' in n:
                a=n['artifact']; data=(run/'bridge/images'/Path(a['path']).name).read_bytes()
                assert hashlib.sha256(data).hexdigest()==a['sha256']
                assert a['source_raw_sha256']==n['sha256'] and v['capture_ns']==n['capture_started_ns']
                links+=1
            for child in v.values(): images(child)
        elif isinstance(v,list):
            for child in v: images(child)
    for q in run.rglob('*.json'): images(json.loads(q.read_text()))
    summary['runs'].append({'run':i,'A1_A2_B1':actual,'task_success':i==2})
summary['image_hash_links']=links
if (p/'MANIFEST.json').exists():
    m=json.loads((p/'MANIFEST.json').read_text())
    assert all(hashlib.sha256((p/k).read_bytes()).hexdigest()==v for k,v in m.items())
print(json.dumps(summary,indent=2))
