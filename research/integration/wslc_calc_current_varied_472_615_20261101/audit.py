import hashlib, json, pathlib, xml.etree.ElementTree as ET

root=pathlib.Path(__file__).resolve().parent
T='{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
O='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'
P='{urn:oasis:names:tc:opendocument:xmlns:text:1.0}'
rows=[]
for ident,count in [('em01',1),('em02',2)]:
    p=root/ident
    config=json.loads((p/'conditions.json').read_text(encoding='utf-8-sig'))
    assert all(hashlib.sha256((p/name).read_bytes()).hexdigest()==expected for name,expected in config['input_sha256'].items())
    result=json.loads((p/'output/result.json').read_text())
    launch=json.loads((p/'launcher-result.json').read_text())
    assert launch['container_exit']==launch['host_exit']==0
    assert not result['keys_down'] and result['buttons']==0
    assert result['close']['release']['verified'] is True
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
    assert calls[-1]['close_returned'] is True
    actions=['click-result.json','recovery-save.json'] if ident=='em01' else ['click-result.json','fresh-entry.json','fresh-save.json']
    for name in actions:
        action=json.loads((p/'output'/name).read_text())
        assert action['status']=='completed'
        releases=action['execution']['releases']; assert releases and all(r['verified'] and not r['keys_down'] and not r['buttons_down'] for r in releases)
    if ident=='em01':
        recovery=json.loads((p/'output/recovery.json').read_text())
        assert result['method']['method_receipt']['outcome']=='SAFE_YIELD'
        assert recovery['original_replay_allowed'] is False and recovery['entry_replayed'] is False and recovery['save_completed'] is True
    rows.append({'allocation':ident,'route':result['route'],'task_seconds':(result['task_end_ns']-result['task_start_ns'])/1e9,
        'launcher_seconds':launch['elapsed_seconds'],'calls':count,
        'input_tokens':sum(c['usage']['input_tokens'] for c in calls),
        'cached_input_tokens':sum(c['usage']['cached_input_tokens'] for c in calls),
        'output_tokens':sum(c['usage']['output_tokens'] for c in calls),
        'saved_values':['472','615'],'neutral':True})
print(json.dumps({'status':'audited','results':rows},indent=2))
