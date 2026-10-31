"""Audit exploratory route outcomes without inferring a model-driven result."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
HERE=Path(__file__).resolve().parent
records={}
for i in range(1,8):
    name=f'e{i:02}'
    with ZipFile(HERE/(name+'.zip')) as z:
        c=json.loads(z.read('conditions.json'));r=json.loads(z.read('output/result.json'))
        assert hashlib.sha256(z.read('runner.py')).hexdigest()==c['runner_sha256']
        assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and r['model_calls']==0
        samples=[json.loads(line) for line in z.read('output/samples.jsonl').splitlines()]
        assert samples==r['samples'] and samples
        assert all(a['tic']<b['tic'] and a['host_ns']<b['host_ns'] for a,b in zip(samples,samples[1:]))
        actions=r.get('actions',[])
        for action in actions:
            assert action['status']=='completed'
            releases=action['execution']['releases']
            assert releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
        if i==4:
            assert r['status']=='error' and 'FlatTargetRefused' in r['error']
            assert 'output/action-turn.json' not in z.namelist()
            assert r['finally_close']['release']['verified']
        else:
            assert r['status']=='completed' and r['keys_down_after']==[]
            assert r['close']['status']=='closed'
            if actions:assert r['close']['release_attempted'] and r['close']['release']['verified']
        records[name]=r
        print(name,r['status'],'samples',len(samples),'actions',len(actions),'final health',samples[-1]['health'])
assert records['e01']['displacement']==0 and records['e01']['model_calls']==0
assert records['e02']['displacement']>5
first_objects=records['e03']['samples'][0]['objects']
assert sum(o['name']=='Zombieman' for o in first_objects)==10
assert sum(o['name']=='DoomImp' for o in first_objects)==1
for name in ('e05','e06'):
    samples=records[name]['samples'];before=next(x for x in samples if x['label']=='forward2');turn=next(x for x in samples if x['label']=='turn')
    if name=='e05':assert before['angle']==turn['angle']
    else:assert before['angle']!=turn['angle']
samples=records['e07']['samples'];visible=next(x for x in samples if 'Zombieman' in x['visible_labels'])
damage=next(x for x in samples if x['health']<samples[0]['health'])
assert visible['tic']<damage['tic'] and samples[0]['health']==100 and samples[-1]['health']==84
assert records['e07']['health_delta']==-16 and records['e07']['kill_delta']==0
print('e07 enemy visible tic',visible['tic'],'first observed damage tic',damage['tic'],'health',samples[-1]['health'])
