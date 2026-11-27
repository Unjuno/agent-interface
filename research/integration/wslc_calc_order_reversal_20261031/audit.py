"""Audit the recorded two-arm pilot, including setup failures."""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json,statistics,xml.etree.ElementTree as ET
T='{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
O='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'

def read(z,p):return json.loads(z.read(p))
def releases(row):
    items=row['execution']['releases']
    return bool(items) and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in items)
def vals(blob):
    sheets=ET.fromstring(blob).findall('.//'+T+'table');assert len(sheets)==1
    rows=sheets[0].findall(T+'table-row');assert len(rows)>=2
    return [r.find(T+'table-cell').get(O+'value') for r in rows[:2]]

measurements={'compiled':[],'fresh':[]}
for name,route,expected_calls in [('c06','compiled',1),('c07','fresh',2),('c08','fresh',2),('c09','compiled',1),('c10','fresh',2),('c11','compiled',1)]:
    path=(Path(__file__).parent.parent/'wslc_calc_matched_guard_pilot_20261031'/(name+'.zip')) if name in ('c06','c07') else Path(__file__).with_name(name+'.zip')
    with ZipFile(path) as z:
        c=read(z,'conditions.json');assert c['route']==route and c['model_calls_max']==expected_calls
        assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and z.read('host.exit').decode('utf-8-sig').strip()=='0'
        for path,expected in c['inputs_sha256'].items():assert hashlib.sha256(z.read(path)).hexdigest()==expected,(name,path)
        result=read(z,'output/result.json');assert result['route']==route
        assert result['saved_score']['pass_effect'] is True and vals(z.read('output/saved.fods'))==['731','864']
        assert not result['keys_down'] and result['buttons']==0
        assert result['close']['release_attempted'] and result['close']['release']['verified']
        assert result['task_start_ns'] < result['method_start_ns'] < result['method_end_ns'] < result['task_end_ns']
        click=read(z,'output/click-result.json');assert click['status']=='completed' and releases(click)
        usage=[];ids=set()
        for i in range(1,expected_calls+1):
            req=read(z,f'exchange/request-{i}.json');resp=read(z,f'exchange/response-{i}.json');raw=read(z,f'model-call-{i}/result.json')
            assert req['id']==resp['id'] and resp['ok'] and resp['attempted']
            assert hashlib.sha256(z.read(f'exchange/image-{i}.png')).hexdigest()==req['image_sha256']==resp['image_sha256']
            assert raw['call_id']==resp['call_id'] and raw['usage']==resp['usage'] and raw['turn_status']=='completed'
            assert raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low'
            assert raw['call_id'] not in ids;ids.add(raw['call_id']);usage.append(raw['usage'])
        if route=='compiled':
            receipt=result['method']['method_receipt'];assert receipt['outcome']=='TASK_SUCCEEDED'
            assert len(receipt['transitions'])==2 and all(x['release_verified'] for x in receipt['transitions'])
            assert read(z,'output/method/saved-effect.json')['verdict']['status']=='succeeded'
        else:
            guard=read(z,'output/fresh-semantic-guard.json');assert guard['events'][0]['event']=='armed' and guard['cue']['cue']=='filled'
            for f in ('output/fresh-entry.json','output/fresh-save.json'):
                row=read(z,f);assert row['status']=='completed' and releases(row)
        ms=(result['method_end_ns']-result['method_start_ns'])/1e6
        inputs=sum(x['input_tokens'] for x in usage);outputs=sum(x['output_tokens'] for x in usage)
        measurements[route].append(((result['task_end_ns']-result['task_start_ns'])/1e6,inputs+outputs))
        print(name,route,'calls',len(usage),'input',inputs,'output',outputs,'input+output',inputs+outputs,'post-grounding phase_ms',round(ms,3),'task_ms',round((result['task_end_ns']-result['task_start_ns'])/1e6,3))

for route,items in measurements.items():
    times=[x[0] for x in items];tokens=[x[1] for x in items]
    print(route,'n',len(items),'task_ms min/median/max',*[round(x,3) for x in (min(times),statistics.median(times),max(times))],'tokens min/median/max',min(tokens),statistics.median(tokens),max(tokens))

paths=[Path(__file__).parent.parent/'wslc_calc_matched_guard_pilot_20261031'/(x+'.zip') for x in ('c06','c07')]+[Path(__file__).with_name(x+'.zip') for x in ('c08','c09','c10','c11')]
with ZipFile(paths[0]) as z: baseline=[z.read(x) for x in ('runner.py','host.py','blank.fods','reference.png')]
for path in paths[1:]:
    with ZipFile(path) as z: assert [z.read(x) for x in ('runner.py','host.py','blank.fods','reference.png')]==baseline
print('all compared runner, host and fixture bytes match')
