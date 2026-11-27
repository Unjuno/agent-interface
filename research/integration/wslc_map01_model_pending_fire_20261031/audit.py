"""Audit model/GUI input, observed game-clock and response-marker evidence."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
HERE=Path(__file__).resolve().parent
records={}
for name,route in [('f01','idle'),('f02','fire')]:
    with ZipFile(HERE/(name+'.zip')) as z:
        def read(path):return json.loads(z.read(path))
        c=read('conditions.json');r=read('output/result.json');e=r['events']
        assert c['route']==route==r['route'] and r['status']=='completed' and r['task_success'] is None
        assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and z.read('host.exit').decode('utf-8-sig').strip()=='0'
        for f,h in c['inputs_sha256'].items():assert hashlib.sha256(z.read(f)).hexdigest()==h
        req=read('exchange/request-1.json');start=read('exchange/started-1.json');done=read('exchange/done-1.json');response=read('exchange/response-1.json');raw=read('model-call-1/result.json')
        assert start['started'] and done['ok'] and response['ok'] and response['close_returned'] and raw['turn_status']=='completed'
        assert req['id']==done['id']==response['id'] and done['call_id']==response['call_id']==raw['call_id']
        assert done['usage']==response['usage']==raw['usage'] and raw['requested_model']=='gpt-6.1-sol'
        assert hashlib.sha256(z.read('exchange/image-1.png')).hexdigest()==req['image_sha256']==done['image_sha256']
        assert r['model_calls']==1 and r['model_done_marker']==done
        s=[json.loads(line) for line in z.read('output/samples.jsonl').splitlines()]
        assert s==r['samples'] and all(a['tic']<b['tic'] and a['host_ns']<b['host_ns'] for a,b in zip(s,s[1:]))
        pending=next(x for x in s if x['label']=='pending-start');finished=next(x for x in s if x['label']=='model-done')
        assert 'Zombieman' in pending['visible_labels'] and pending['tic']<finished['tic']
        assert e['request_published_ns']<e['model_start_marker_observed_ns']<e['model_done_marker_observed_ns']
        for action in r['actions']:
            assert action['status']=='completed';releases=action['execution']['releases']
            assert releases and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in releases)
        assert r['keys_down_after']==[] and r['close']['release_attempted'] and r['close']['release']['verified']
        assert pending['health']==100 and finished['health']==100
        if route=='idle':
            assert len(r['actions'])==2 and finished['kills']==0
        else:
            assert len(r['actions'])==3 and e['model_start_marker_observed_ns']<e['fire_started_ns']<e['fire_finished_ns']<e['model_done_marker_observed_ns']
            fire=read('output/action-fire.json');assert fire['execution']['program_emissions']==2
            kills=[x for x in s if x['label']=='pending' and x['kills']>=1]
            assert kills and kills[0]['host_ns']<e['model_done_marker_observed_ns'] and finished['kills']==1
            assert any(x['label']=='pending' and kills[0]['host_ns']<x['host_ns']<e['model_done_marker_observed_ns'] for x in s)
            print('fire: first observed kill tic',kills[0]['tic'],'model done observed at tic',finished['tic'])
        records[route]=r
        print(name,route,'pending tics',pending['tic'],'to',finished['tic'],'health',pending['health'],'to',finished['health'],'kills',pending['kills'],'to',finished['kills'],'model_ms',round(done['runner_ns']/1e6,3),'tokens',done['usage']['input_tokens']+done['usage']['output_tokens'])
assert records['idle']['iwad_sha256']==records['fire']['iwad_sha256']
print('two routes share IWAD; event ordering uses container-side marker observation')
