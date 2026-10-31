"""Read-only audit of all MAP01 control and diagnostic allocations."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,math
HERE=Path(__file__).resolve().parent
with ZipFile(HERE/'d01.zip') as z:
    assert z.read('container.exit').decode('utf-8-sig').strip()=='139'
    assert b'Read-only file system' in z.read('container.stderr')
for name in ('d02','d04'):
    with ZipFile(HERE/(name+'.zip')) as z:assert 'container.exit' not in z.namelist()
with ZipFile(HERE/'d03.zip') as z:
    r=json.loads(z.read('output/result.json'));assert r['status']=='error' and 'keyboard continuation requires explicit keyboard input' in r['error']
results={}
for name,route in [('d05','wait'),('d06','forward')]:
    with ZipFile(HERE/(name+'.zip')) as z:
        c=json.loads(z.read('conditions.json'));r=json.loads(z.read('output/result.json'));a=json.loads(z.read('output/action.json'))
        assert c['route']==r['route']==route and hashlib.sha256(z.read('runner.py')).hexdigest()==c['runner_sha256']
        assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['task_success'] is None
        assert r['model_calls']==0 and r['w_down_after'] is False
        samples=[json.loads(x) for x in z.read('output/samples.jsonl').splitlines()]
        assert samples==r['samples'] and len(samples)>=3
        assert samples[0]['label']=='before' and samples[1]['label']=='after'
        assert all(x['tic']<y['tic'] and x['host_ns']<y['host_ns'] for x,y in zip(samples,samples[1:]))
        before,after,last=samples[0],samples[1],samples[-1]
        movement=math.dist([before['x'],before['y']],[after['x'],after['y']])
        coast=math.dist([after['x'],after['y']],[last['x'],last['y']])
        assert abs(movement-r['displacement'])<1e-8
        assert r['health_delta']==last['health']-before['health'] and r['kill_delta']==last['kills']-before['kills']
        assert r['close']['status']=='closed'
        if route=='wait':assert a['status']=='no_input_control' and a['input_dispatched'] is False and not r['close']['release_attempted']
        else:
            assert a['status']=='completed' and a['execution']['program_emissions']==2
            releases=a['execution']['releases'];assert releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
            assert releases[-1]['monotonic_ns']<after['host_ns']
            assert r['close']['release_attempted'] and r['close']['release']['verified']
        obs=r['observation']['native']['artifact'];parts=Path(obs['path']).parts;arc='output/'+'/'.join(parts[2:]);assert hashlib.sha256(z.read(arc)).hexdigest()==obs['sha256']
        results[route]=(movement,coast,r['health_delta'],r['kill_delta'],r['iwad_sha256'])
        print(name,route,'input interval displacement',round(movement,3),'post-interval displacement',round(coast,3),'health change',r['health_delta'],'kill change',r['kill_delta'])
assert results['wait'][4]==results['forward'][4]
assert results['wait'][0]==0 and results['forward'][0]>5
print('d01/d03 failures retained; d02/d04 unrun; matching IWAD')
