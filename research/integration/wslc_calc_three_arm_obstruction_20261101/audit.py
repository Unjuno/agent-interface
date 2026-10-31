import hashlib, json, pathlib, xml.etree.ElementTree as ET
from PIL import Image

root=pathlib.Path(__file__).resolve().parent
T='{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
O='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'
P='{urn:oasis:names:tc:opendocument:xmlns:text:1.0}'
rows=[]; owner_sessions=[]; call_ids=[]
for ident,count in [('eq01',2),('eq02',2),('eq03',3)]:
    p=root/ident
    config=json.loads((p/'conditions.json').read_text(encoding='utf-8-sig'))
    assert config['order']==['eq01:direct','eq02:compiled','eq03:fresh']
    assert config['route']=={'eq01':'direct','eq02':'compiled','eq03':'fresh'}[ident]
    assert config['freeze_main']=='d24b6ff1fb560e7ea0be35f4e7b8281c4a4e6f7a'
    assert '472/615' in config['pass_condition'] and 'no success retry' in config['stop_rule']
    assert all(hashlib.sha256((p/name).read_bytes()).hexdigest()==expected for name,expected in config['input_sha256'].items())
    result=json.loads((p/'output/result.json').read_text())
    gate=json.loads((p/'output/stale-gate.json').read_text())
    assert gate['binding_unchanged'] is True and gate['prior_programs_or_mints']==[]
    assert gate['before_sha256']!=gate['after_sha256']
    x,y=gate['point']
    for sequence,expected in ((gate['first_sequence'],gate['before_sha256']),
                              (gate['stale_sequence'],gate['after_sha256'])):
        matches=list((p/'output/owner').rglob(f'observation-{sequence}.json')); assert len(matches)==1
        observation=json.loads(matches[0].read_text()); artifact=observation['native']['artifact']
        image=p/'output'/artifact['path'].removeprefix('/out/')
        data=image.read_bytes(); assert hashlib.sha256(data).hexdigest()==artifact['sha256']
        rgb=Image.open(image).convert('RGB')
        assert artifact['source_raw_sha256']==observation['native']['sha256']
        assert hashlib.sha256(rgb.crop((x-4,y-4,x+4,y+4)).tobytes()).hexdigest()==expected
    assert gate['stale_sequence']>gate['first_sequence']
    second_request=json.loads((p/'exchange/request-2.json').read_text())
    assert second_request['source_sequence']>gate['stale_sequence']
    launch=json.loads((p/'launcher-result.json').read_text())
    assert launch['container_exit']==launch['host_exit']==0
    assert not result['keys_down'] and result['buttons']==0
    assert result['close']['release']['verified'] is True
    owner_sessions.append(result['close']['session_id'])
    tree=ET.fromstring((p/'output/saved.fods').read_bytes())
    tables=tree.findall('.//'+T+'table'); assert len(tables)==1
    direct=tables[0].findall(T+'table-row'); assert len(tables[0].findall('.//'+T+'table-row'))==len(direct)
    cells=[]; y=0
    for row in direct:
        row_repeat=int(row.get(T+'number-rows-repeated','1')); assert row_repeat>0
        x=0
        for c in row:
            if c.tag not in (T+'table-cell',T+'covered-table-cell'): continue
            repeat=int(c.get(T+'number-columns-repeated','1')); assert repeat>0
            v=c.get(O+'value'); kind=c.get(O+'value-type'); formula=c.get(T+'formula'); text=''.join(c.itertext()).strip()
            if v is not None or kind is not None or formula is not None or text:
                assert row_repeat==repeat==1
                cells.append([y,x,kind,v,text,formula])
            x+=repeat
        y+=row_repeat
    assert cells==[[0,0,'float','472','472',None],[1,0,'float','615','615',None]]
    calls=[]
    for i in range(1,count+1):
        response=json.loads((p/f'exchange/response-{i}.json').read_text())
        request=json.loads((p/f'exchange/request-{i}.json').read_text())
        image=(p/f'exchange/image-{i}.png').read_bytes()
        assert response['ok'] is True and response['id']==request['id']
        assert response['image_sha256']==request['image_sha256']==hashlib.sha256(image).hexdigest()
        calls.append(response)
        call_ids.append(response['call_id'])
    assert calls[-1]['close_returned'] is True
    actions=['click-result.json','recovery-save.json'] if ident=='eq02' else ['click-result.json','fresh-entry.json','fresh-save.json']
    for name in actions:
        action=json.loads((p/'output'/name).read_text())
        assert action['status']=='completed'
        releases=action['execution']['releases']; assert releases and all(r['verified'] and not r['keys_down'] and not r['buttons_down'] for r in releases)
    if ident=='eq02':
        recovery=json.loads((p/'output/recovery.json').read_text())
        assert result['method']['method_receipt']['outcome']=='SAFE_YIELD'
        assert recovery['original_replay_allowed'] is False and recovery['entry_replayed'] is False and recovery['save_completed'] is True
    rows.append({'allocation':ident,'route':result['route'],'task_seconds':(result['task_end_ns']-result['task_start_ns'])/1e9,
        'launcher_seconds':launch['elapsed_seconds'],'calls':count,
        'input_tokens':sum(c['usage']['input_tokens'] for c in calls),
        'cached_input_tokens':sum(c['usage']['cached_input_tokens'] for c in calls),
        'output_tokens':sum(c['usage']['output_tokens'] for c in calls),
        'saved_values':['472','615'],'neutral':True})
assert len(set(owner_sessions))==3 and len(set(call_ids))==7
print(json.dumps({'status':'audited','results':rows},indent=2))
