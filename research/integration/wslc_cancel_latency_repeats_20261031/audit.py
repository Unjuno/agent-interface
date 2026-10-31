"""Audit every preplanned sample; no replacement or filtering of failures."""
from pathlib import Path
from zipfile import ZipFile
import hashlib, json, statistics, xml.etree.ElementTree as ET
T='{urn:oasis:names:tc:opendocument:xmlns:table:1.0}'
O='{urn:oasis:names:tc:opendocument:xmlns:office:1.0}'

def values(blob):
    sheets=ET.fromstring(blob).findall('.//'+T+'table')
    assert len(sheets)==1
    rows=sheets[0].findall(T+'table-row')
    assert len(rows)>=2
    return [r.find(T+'table-cell').get(O+'value') for r in rows[:2]]

wait_ms=[]; cancel_end=[]; cancel_observed=[]
for i in range(1,9):
    with ZipFile(Path(__file__).with_name(f'b{i:02}.zip')) as z:
        def read(path):return json.loads(z.read(path))
        c=read('conditions.json'); assert c['sample_index']==i and c['planned_count']==8
        assert c['cancel_requested']==(i%2==0)
        for path,expected in c['inputs_sha256'].items():
            assert hashlib.sha256(z.read(path)).hexdigest()==expected, (i,path)
        assert z.read('container.exit').decode('utf-8-sig').strip()=='0'
        first=read('output/mcp-initial.json');terminal=read('output/mcp-terminal.json');r=read('output/result.json')
        assert first['status']=='pending' and first['call_id']==r['call_id']
        ex=terminal['result']['execution'];w=ex['waits'][0]
        assert w['requested_ms']==2000
        assert ex['releases'] and all(x['verified'] and not x['keys_down'] and not x['buttons_down'] for x in ex['releases'])
        assert not r['keys_down'] and r['buttons_after']==0
        mid=z.read('output/mid.fods');after=z.read('output/after.fods')
        assert hashlib.sha256(mid).hexdigest()==r['baseline_sha256'] and values(mid)==[None,None]
        assert values(after)==['731','864'] and r['after_score']['pass_effect'] is True
        if i%2:
            assert terminal['status']=='completed' and w['completed'] and 3 in ex['completed_ops']
            elapsed=(w['ended_ns']-w['started_ns'])/1e6;wait_ms.append(elapsed)
            print(f'b{i:02} control wait_ms={elapsed:.3f}')
        else:
            cancel=read('output/mcp-cancel.json');request=cancel['requested_ns']
            assert cancel['response']['status']=='cancel_requested'
            assert terminal['status']=='execution_failed' and not w['completed'] and ex['failed_op']==2
            assert w['started_ns'] <= request <= w['ended_ns'] <= ex['ended_ns'] <= r['terminal_ns']
            a=(ex['ended_ns']-request)/1e6;b=(r['terminal_ns']-request)/1e6
            cancel_end.append(a);cancel_observed.append(b)
            print(f'b{i:02} cancel request_to_execution_end_ms={a:.3f} request_to_client_terminal_ms={b:.3f}')
for name,items in [('control_wait_ms',wait_ms),('cancel_request_to_execution_end_ms',cancel_end),('cancel_request_to_client_terminal_ms',cancel_observed)]:
    print(name,'n=',len(items),'min=',round(min(items),3),'median=',round(statistics.median(items),3),'max=',round(max(items),3))

