from pathlib import Path
from zipfile import ZipFile
import hashlib,json,statistics,xml.etree.ElementTree as ET
T='{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
O='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'
def read(z,p): return json.loads(z.read(p))
def release(row):
    items=row['execution']['releases']
    return bool(items) and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in items)
def vals(blob):
    sheets=ET.fromstring(blob).findall('.//'+T+'table'); assert len(sheets)==1
    sheet=sheets[0]; rows=sheet.findall(T+'table-row')
    assert len(rows)==len(sheet.findall('.//'+T+'table-row'))
    populated=[]; row_index=0
    for row in rows:
        repeat=int(row.get(T+'number-rows-repeated','1')); assert repeat>0
        column=0
        for cell in row:
            if cell.tag not in (T+'table-cell',T+'covered-table-cell'): continue
            count=int(cell.get(T+'number-columns-repeated','1')); assert count>0
            kind=cell.get(O+'value-type'); value=cell.get(O+'value'); formula=cell.get(T+'formula'); text=''.join(cell.itertext()).strip()
            if kind is not None or value is not None or formula is not None or text:
                assert repeat==1 and count==1
                populated.append((row_index,column,kind,value,text,formula))
            column+=count
        row_index+=repeat
    return populated
measurements={'compiled':[],'fresh':[]}; threads=set(); baseline=None
for name,route,count in [('gg01','fresh',2),('gg02','compiled',1),('gg03','compiled',1),('gg04','fresh',2)]:
    with ZipFile(Path(__file__).with_name(name+'.zip')) as z:
        c=read(z,'conditions.json'); assert c['allocation']==name and c['route']==route and c['calls_max']==count
        assert c['order']==['gg01:fresh','gg02:compiled','gg03:compiled','gg04:fresh']
        assert c['session']=='one persistent session per arm' and c['model']=='gpt-6.1-sol low'
        assert c['image']=='sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25' and c['cpu']==1 and c['memory']=='1g'
        for f in ('container.exit','host.exit'): assert z.read(f).decode('utf-8-sig').strip()=='0'
        hashes=read(z,'input-hashes.json')
        for f,h in hashes.items(): assert hashlib.sha256(z.read(f)).hexdigest()==h
        if baseline is None: baseline=hashes
        else: assert hashes==baseline
        result=read(z,'output/result.json'); assert result['route']==route and result['saved_score']['pass_effect'] and vals(z.read('output/saved.fods'))==[(0,0,'float','731','731',None),(1,0,'float','864','864',None)]
        assert not result['keys_down'] and result['buttons']==0
        assert result['close']['status']=='closed' and result['close']['release_attempted'] and result['close']['release']['verified']
        assert not result['close']['release']['keys_down'] and not result['close']['release']['buttons_down']
        assert result['task_start_ns']<result['method_start_ns']<result['method_end_ns']<result['task_end_ns']
        click=read(z,'output/click-result.json'); assert click['status']=='completed' and release(click)
        usage=[]; ids=set(); session=None
        for i in range(1,count+1):
            req=read(z,f'exchange/request-{i}.json'); resp=read(z,f'exchange/response-{i}.json'); raw=read(z,f'model-call-{i}/result.json')
            assert req['id']==resp['id'] and resp['ok'] and resp['attempted']
            assert hashlib.sha256(z.read(f'exchange/image-{i}.png')).hexdigest()==req['image_sha256']==resp['image_sha256']
            assert raw['call_id']==resp['call_id'] and raw['usage']==resp['usage'] and raw['turn_status']=='completed'
            assert raw['requested_model']=='gpt-6.1-sol' and raw['requested_effort']=='low'
            assert raw['call_id'] not in ids; ids.add(raw['call_id']); usage.append(raw['usage'])
            if session is None: session=raw['thread_id']
            else: assert raw['thread_id']==session
            assert resp.get('close_returned', False)==(i==count)
            assert 0<=raw['usage']['cached_input_tokens']<=raw['usage']['input_tokens']
        assert session not in threads; threads.add(session)
        if route=='compiled':
            receipt=result['method']['method_receipt']; assert receipt['outcome']=='TASK_SUCCEEDED'
            assert len(receipt['transitions'])==2 and all(x['release_verified'] for x in receipt['transitions'])
            assert read(z,'output/method/saved-effect.json')['verdict']['status']=='succeeded'
        else:
            assert result['method']['status']=='completed'
            guard=read(z,'output/fresh-semantic-guard.json'); assert guard['events'][0]['event']=='armed' and guard['cue']['cue']=='filled'
            for f in ('output/fresh-entry.json','output/fresh-save.json'):
                row=read(z,f); assert row['status']=='completed' and release(row)
        seconds=(result['task_end_ns']-result['task_start_ns'])/1e9
        totals=[sum(x[k] for x in usage) for k in ('input_tokens','cached_input_tokens','output_tokens')]
        measurements[route].append((seconds,totals[0]+totals[2])); print(name,route,'seconds',round(seconds,3),'input cached output',*totals)
for route,items in measurements.items():
    print(route,'n',len(items),'median seconds',round(statistics.median(x[0] for x in items),4),'median input+output',statistics.median(x[1] for x in items))
a=statistics.median(x[0] for x in measurements['compiled']); b=statistics.median(x[0] for x in measurements['fresh'])
print('compiled median measured interval reduction percent',round((1-a/b)*100,2))
print('PASS: result, release, call/session linkage and matching input hashes; omitted private files are hash-indexed, not audited')
