"""Audit fresh field task, preserved state values and pre-score GUI commitment."""
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from audit_cause_servo_v2 import frames,read
from decision_receipt_v4 import build as receipt
from input_state_table_v1 import build,decode,selected,canonical
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent;root=HERE/'results/field-table-live-01';runtime=root/'runtime'
plan=read(root/'initial/plan.json')
for name,sha in plan['sources'].items():assert digest((HERE/name).read_bytes())==sha
for name,sha in read(runtime/'sources.json').items():assert digest((HERE.parent/name).read_bytes())==sha
raw=[json.loads(line) for line in (runtime/'events.jsonl').read_text().splitlines()]
covered=set();exchanges=0
for stage in ('initial','select','edit','save','decide','finish'):
    for path in sorted((root/stage).glob('query-*-request.json')):
        q,r=read(path),read(path.with_name(path.name.replace('-request','-reply')))
        a,b=q['after'],r['cursor'];assert b-a==len(r['records']) and r['records']==raw[a:b] and r['status']=='boundary'
        assert not covered.intersection(range(a,b));covered.update(range(a,b));exchanges+=1
        if 'command' in q:
            echo=dict(q['command'],transport_request_id=q['request_id'])
            assert sum(e['event']=='command' and e['command']==echo for e in r['records'])==1
assert covered==set(range(len(raw)))
owners=read(runtime/'owner-events.json');sizes=[]
for stage in ('select','edit','save'):
    data=(root/stage/'report.json').read_bytes();report=json.loads(data)
    states=read(root/stage/'state-table.json');review=read(root/stage/'receipt.json')
    assert build(data)==states and receipt(data)==review
    assert canonical(decode(states['table']))==canonical(selected(report))
    assert review['program_binding'] is not None and review['detail_review_required']
    release=report['terminal']['release']
    assert report['terminal']['status']=='completed' and release in owners
    assert release['verified'] and not release['buttons_down'] and not release['keys_down']
    delivered=read(root/stage/'result.json')
    assert delivered['receipt']==review and delivered['state_table']==states
    sizes.append(dict(stage=stage,selected_rows_bytes=len(canonical(selected(report)).encode()),
                      full_companion_bytes=len(canonical(states).encode()),observations=len(states['table']['observations'])))
commit=read(root/'decide/commit.json');decision=read(root/'gui-decision.json')
assert digest((root/'gui-decision.json').read_bytes())==commit['sha256']
assert decision==read(root/'decide/decision.json') and decision['task_met'] is True
assert digest((root/'save/report.json').read_bytes())==commit['report_sha256']
assert decision['image_sha256']==commit['image']['sha256']==digest((runtime/Path(commit['image']['path']).name).read_bytes())
matches=[(i,e) for i,e in enumerate(raw) if e['event']=='command' and e['command'].get('gui_decision_sha256')==commit['sha256']]
assert len(matches)==1;index,echo=matches[0]
assert raw[index+1]['event']=='clock' and raw[index+1]['sequence']==commit['image']['sequence']
assert not any(e['event']=='independent_evaluation' for e in raw[:index+1])
svg=ET.parse(runtime/'shape.svg').getroot();rects=list(svg.iter('{http://www.w3.org/2000/svg}rect'))
assert len(rects)==1 and rects[0] in list(svg) and not any('transform' in e.attrib for e in svg.iter())
actual={k:float(rects[0].get(k)) for k in plan['target']}
checks={k:math.isfinite(actual[k]) and abs(actual[k]-target)<=plan['absolute_tolerance'] for k,target in plan['target'].items()}
assert all(checks.values()) and actual==decision['displayed_geometry']
observations=frames(runtime,raw)
assert raw[-1]['event']=='independent_evaluation' and raw[-1]['success']
result=dict(audit_passed=True,audit_sha256=digest(Path(__file__).read_bytes()),events=len(raw),socket_exchanges=exchanges,
            exact_frames=len(observations),selected_state_sizes=sizes,strict_score=dict(success=all(checks.values()),actual=actual,checks=checks,
            target=plan['target'],tolerance=plan['absolute_tolerance'],svg_sha256=digest((runtime/'shape.svg').read_bytes()),scope='single direct untransformed rectangle geometry; not full SVG equivalence'),
            initial_capture_to_gui_decision_seconds=(echo['received_ns']-observations[0]['capture_ns'])/1e9,
            initial_capture_to_final_evaluation_seconds=(raw[-1]['known_ns']-observations[0]['capture_ns'])/1e9,
            limits='One changed-value, familiar-layout live trial without injected fault. No matched speed/token comparison or independent per-child cleanup inventory. Table replaces extra state dump; receipt attention remains.')
with (root/'audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
