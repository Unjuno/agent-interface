import base64, hashlib, io, json, math, tarfile, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

def require(ok, message):
    if not ok: raise ValueError(message)

def audit(data):
    b = 'results-local/reviewed-image-pair-01/'
    load = lambda name: json.loads(data[b+name])
    plan = load('plan.json'); result = load('result.json')
    require(plan['seed']==991357 and plan['order']==['B0-full','C1-reviewed-reference'], 'fixed plan')
    for name,digest in plan['source_sha256'].items():
        require(hashlib.sha256(data[name]).hexdigest()==digest, 'source pin '+name)
    for name in ('native_relay_client_v1.mjs','relay_host_timeline_v1.mjs'):
        require(data[b+'host-source/'+name]==data['research/live_control/'+name], 'loaded host identity')
    require(hashlib.sha256(data['results-local/reviewed-image-pair-fixture.py']).hexdigest()==data[b+'fixture-sha256.txt'].decode().strip(), 'fixture pin')
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    arm_ops={}; initial_images={}
    for arm in plan['order']:
        prefix=arm+'/'
        get=lambda name:load(prefix+name)
        expected=result['arms'][arm]
        require(get('allocation.json')['source']==plan['source_commit'] and get('allocation.json')['seed']==plan['seed'], 'allocation')
        require(get('goal.json')=={'A1':324,'A2':145}, 'same task')
        require(expected['saved_values']==[324,145], 'claimed saved values')
        require(get('evaluation.json')=={'actual':[324,145],'expected':[324,145],'success':True}, 'saved evaluation')
        with zipfile.ZipFile(io.BytesIO(data[b+prefix+'saved.xlsx'])) as z:
            root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        cells={c.attrib['r']:c.find('s:v',ns).text for c in root.findall('.//s:c',ns) if c.find('s:v',ns) is not None}
        require(cells.get('A1')=='324' and cells.get('A2')=='145', 'saved XML')
        events=[json.loads(x) for x in data[b+prefix+'host/host-events.jsonl'].splitlines()]
        events_by={}; sends={}; replies={}; reviews={}; base=None; active=None; last=None; clock=-1
        for index,e in enumerate(events,1):
            require(type(e['sequence']) is int and e['sequence']==index, 'event sequence')
            stamp=e['host_monotonic_ms']
            require(type(stamp) in (int,float) and math.isfinite(stamp) and stamp>=clock, 'event clock')
            clock=stamp; kind=e['kind']; i=e.get('attempt')
            if kind=='send_requested':
                require(i not in sends, 'duplicate send'); sends[i]=stamp
            elif kind=='reply_available':
                raw=data[b+prefix+f'host/reply-{i}.json']
                require(hashlib.sha256(raw).hexdigest()==e['reply_sha256'], 'reply binding')
                value=json.loads(raw); require(value['status']=='returned' and value['id']==i, 'returned identity')
                if value['result'].get('isError'):
                    body=json.loads(next(c['text'] for c in value['result']['content'] if c['type']=='text'))
                    require(value['tool']=='interface_inspect_target' and body.get('status')=='needs_review'
                            and body.get('error') is None and body.get('input_dispatched') is False
                            and body.get('image_status')=='image' and body.get('review_request',{}).get('tool')=='interface_review_target'
                            and body.get('observation_report',{}).get('status')=='returned', 'unexpected tool failure')
                replies[i]=(stamp,value)
            elif kind=='presentation_started':
                require(active is None and i in replies, 'presentation start')
                require(e['reply_sha256']==hashlib.sha256(data[b+prefix+f'host/reply-{i}.json']).hexdigest(), 'presentation hash')
                delivery=e.get('image_delivery',{'mode':'full'})
                require(('image_delivery' in e)==(arm=='C1-reviewed-reference'), 'arm mode')
                pics=[c for c in replies[i][1]['result']['content'] if c['type']=='image']
                if delivery['mode']=='reviewed-image-reference':
                    require(base is not None and delivery==base[0], 'acknowledged base')
                    require(len(pics)==1 and pics[0]['data']==base[1], 'reference bytes')
                else: require(delivery=={'mode':'full'}, 'full shape')
                active=(i,delivery,pics)
            elif kind=='presentation_callbacks_completed':
                require(active is not None and active[:2]==(i,e.get('image_delivery',{'mode':'full'})), 'completed presentation')
                last=active; active=None; events_by[i]=last
                if last[1]['mode']=='full':base=None
            elif kind=='review_recorded':
                require(last is not None and last[0]==i, 'review latest presentation')
                require(e.get('image_delivery',{'mode':'full'})==last[1], 'review delivery')
                receipt=get(f'host/review-{i}.json')
                require(receipt['phase']==e['phase'] and receipt['source_sequence'] is None, 'review identity')
                require(receipt['reply_sha256']==hashlib.sha256(data[b+prefix+f'host/reply-{i}.json']).hexdigest(), 'review reply hash')
                require(len(last[2])==1, 'review image')
                pic=last[2][0]; digest=hashlib.sha256(base64.b64decode(pic['data'],validate=True)).hexdigest()
                require(receipt['images']==[{'mime_type':'image/png','sha256':digest}], 'review image hash')
                reviews[e['phase']]=stamp
                if last[1]['mode']=='full':
                    base=({'mode':'reviewed-image-reference','base_attempt':i,'base_reply_sha256':receipt['reply_sha256'],
                           'base_review_sha256':hashlib.sha256(data[b+prefix+f'host/review-{i}.json']).hexdigest(),
                           'image_sha256':digest,'mime_type':'image/png'},pic['data'])
        require(active is None and events[-1]['kind']=='transport_closed', 'closed timeline')
        n=len(sends);require(set(sends)==set(range(1,n+1)) and len(replies)==n and len(events_by)==n, 'all boundaries')
        rows=[]; ops=[]; reports={}
        for i in range(1,n+1):
            request=get(f'host/request-{i}.json');value=replies[i][1]
            require(request['id']==value['id'] and request['tool']==value['tool'], 'request identity')
            content=value['result']['content'];delivery=events_by[i][1];pics=events_by[i][2]
            reports[i]=json.loads(next(c['text'] for c in content if c['type']=='text'))
            rows.append({'attempt':i,'tool':request['tool'],'image_count':len(pics),'mode':delivery['mode'],'base_attempt':delivery.get('base_attempt'),
                         'png_bytes':sum(len(base64.b64decode(c['data'],validate=True)) for c in pics),
                         'original_text_bytes':sum(len(c['text'].encode()) for c in content if c['type']=='text')})
            if request['tool']=='interface_dispatch':
                program=request['arguments']['program']
                require(program['schema']=='agent-interface/program-v1' and program['terminal']=={'release_all_required':True}, 'program contract')
                require(request['arguments']['compact'] is True and request['arguments']['report_refs'] is True, 'presentation arguments')
                ops.append({'program_id':program['program_id'],'source':program['source'],'ops':program['ops'],
                            'current_observation_seq':request['arguments']['current_observation_seq'],
                            'current_binding_revision':request['arguments']['current_binding_revision']})
                summary=reports[i]['outcome_summary']
                require(summary['execution_status']=='completed' and summary['input_release_verified'] is True and summary['recovery_required'] is False, 'dispatch result')
        require(rows==expected['rows'] and ops==expected['input_programs'], 'derived rows/programs')
        require(len(ops)==expected['dispatch_count']==3, 'dispatch count')
        require(n==expected['call_count']==(9 if arm=='B0-full' else 8), 'call count')
        require(sum(x['image_count'] for x in rows)==expected['image_reply_count'], 'image count')
        require(sum(x['image_count'] for x in rows if x['mode']=='full')==expected['full_image_count'], 'full count')
        require(sum(x['mode']=='reviewed-image-reference' for x in rows)==expected['reference_count'], 'reference count')
        require(sum(x['png_bytes'] for x in rows if x['mode']=='reviewed-image-reference')==expected['omitted_png_bytes'], 'omitted bytes')
        require(n-8==expected['extra_observations']==get('finish.json')['extra_observations'], 'extra observations')
        offered=reports[4]['review_request'];submitted=get('host/request-5.json')
        require(submitted['tool']==offered['tool'] and submitted['arguments']==offered['arguments'], 'exact target selection')
        require(reports[5]['binding_revision']==2 and reports[5]['capture_consistency']=='matched', 'binding result')
        require(reports[n]['status']=='closed' and reports[n]['release']['verified'] is True and get('host/exit.json')['code']==0, 'cleanup')
        require(expected['cleanup']==get('cleanup.json'), 'fixture teardown')
        measured={'sum_send_to_reply':sum(replies[i][0]-sends[i] for i in sends),
                  'enter_send_to_declared_review':reviews['entered-verified']-sends[2],
                  'confirm_send_to_saved_declaration':reviews['saved-visible']-sends[6],
                  'first_send_to_saved_declaration':reviews['saved-visible']-sends[1]}
        for key,value in measured.items():
            require(abs(value-expected['host_timing_ms'][key])<1e-6, 'derived timing '+key)
        timing=get('host-timing.json')
        require(timing['call_count']==n and timing['timeline_status']=='complete', 'timing summary')
        for name,digest in timing['input_sha256'].items():
            require(hashlib.sha256(data[b+prefix+'host/'+name]).hexdigest()==digest, 'timing input identity')
        arm_ops[arm]=ops
        initial_images[arm]=[events_by[i][2][0]['data'] for i in (1,2,3)]
    require(arm_ops['B0-full']==arm_ops['C1-reviewed-reference'] and result['identical_input_programs'] is True, 'matched input operations')
    require(initial_images['B0-full']==initial_images['C1-reviewed-reference'], 'matched first three images')
    require(result['status']=='FUNCTIONAL_PAIR_PASS_EFFICIENCY_HOLD', 'scope')
    return result

def main():
    p=Path(__file__).resolve().parent; m=json.loads((p/'manifest.json').read_text())
    with tarfile.open(p/'raw.tar.gz') as t:
        members=[x for x in t.getmembers() if x.isfile()]
        require(len(set(x.name for x in members))==len(members), 'duplicate archive members')
        data={x.name:t.extractfile(x).read() for x in members}
    require(set(data)==set(m['files']), 'archive members')
    for name,raw in data.items():
        require({'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}==m['files'][name], 'file identity '+name)
    for name in ('plan.json','result.json'):
        require((p/name).read_bytes()==data['results-local/reviewed-image-pair-01/'+name], 'published copy')
    require(hashlib.sha256((p/'plan.json').read_bytes()).hexdigest()==m['plan_sha256'], 'plan identity')
    audit(data)
    print(f'PASS: {len(data)} files; matched input programs; both saved 324/145; B0 9 calls/7 full, C1 8 calls/4 full/2 references; efficiency HOLD')

if __name__=='__main__':main()
