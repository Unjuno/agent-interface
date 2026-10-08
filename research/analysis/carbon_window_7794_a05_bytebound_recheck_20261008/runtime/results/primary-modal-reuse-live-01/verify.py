import base64,copy,hashlib,json
from pathlib import Path
from openpyxl import load_workbook
root=Path(__file__).resolve().parent
def require(ok,message):
    if not ok:raise ValueError(message)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def audit(d):
    rows=d['rows'];meta=d['meta'];req=d['requests'];case=d['case'];reuse=d['reuse']
    require([r['status'] for r in rows]==['ready']+['returned']*13+['terminal'],'stream order')
    require([r['result']['id'] for r in rows[1:-1]]==list(range(1,14)),'command ids')
    require(all(r['result']['caller_state']['stopped'] is None for r in rows[1:-1]),'hidden stop')
    require(req[9]['args'][1]==meta[7]['review_request']['arguments'],'one-use target selection')
    require(meta[7]['input_dispatched'] is False and meta[7]['authority_granted'] is False,'inspect grants authority')
    require(meta[9]['binding_revision']==2 and meta[9]['status']=='target_reviewed' and meta[9]['capture_consistency']=='matched','target revision')
    require(req[11]['args'][1]['current_binding_revision']==2,'stale input binding')
    for command in (5,11):
        m=meta[command];require(m['outcome_summary']['execution_status']=='completed','input incomplete')
        releases=m['receipt']['execution_summary']['releases']
        require(releases and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in releases),'nonneutral input')
        require(m['receipt']['execution_summary']['started_ns']<req[command]['args'][1]['program']['authority']['expires_at_ns'],'input after expiry')
    require(meta[13]['status']=='closed' and meta[13]['release']==d['close_release'],'close identity')
    require(d['close_release']['verified'] is True and d['close_release']['keys_down']==[] and d['close_release']['buttons_down']==[],'nonneutral close')
    require(rows[-1]['exit']=={'code':0,'signal':None} and d['cleanup']['host_exit']==0,'unterminated transport')
    require(d['cells']=={'A1':317,'A2':529} and d['score']['actual_nonempty_cells']==d['cells'] and d['score']['success'] is True,'saved effect')
    total=0;references=[]
    for command,attempt in ((1,1),(5,3),(7,4),(9,5),(11,6)):
        result=rows[command]['result'];raw=base64.b64decode(next(b['data'] for b in d['reply'][command]['result']['content'] if b['type']=='image'),validate=True)
        markers=[x for x in result['presented_text'] if isinstance(x,dict) and x.get('schema')=='agent-interface/reviewed-image-reference-v1']
        total+=len(result['images'])
        require(d['reviews'][attempt]['reply_sha256']==sha(case/'host'/f'reply-{attempt}.json'),'review source')
        if reuse and command in (7,9):
            require(not result['images'] and len(markers)==1,'reference not presented')
            marker=markers[0];references.append(marker)
            require(marker['attempt']==attempt and marker['base_attempt']==3,'wrong reference attempt')
            require(marker['reply_sha256']==sha(case/'host'/f'reply-{attempt}.json'),'reference current identity')
            require(marker['base_reply_sha256']==sha(case/'host'/'reply-3.json') and marker['base_review_sha256']==sha(case/'host'/'review-3.json'),'reference base identities')
            require(marker['image_sha256']==hashlib.sha256(raw).hexdigest() and raw==(case/'exchange'/'image-5-1.png').read_bytes(),'reference PNG identity')
        else:
            require(not markers and len(result['images'])==1,'missing full PNG')
            image=result['images'][0]
            require(Path(image['path']).read_bytes()==raw and image['sha256']==hashlib.sha256(raw).hexdigest(),'full PNG identity')
    require(total==(3 if reuse else 5),'image count')
    events=d['events'];timing=d['timing']
    return {'arm':'reuse' if reuse else 'full','task_success':True,'public_requests':7,'primary_commands':13,
      'native_reply_images':5,'delivered_images':total,'references':len(references),'input_programs':2,
      'first_send_to_last_reply_ms':timing['first_send_to_last_reply_ms'],
      'first_send_to_transport_close_ms':events[-1]['host_monotonic_ms']-events[0]['host_monotonic_ms'],
      'owner_ready_to_all_children_terminal_ms':(d['cleanup']['ended_ns']-d['owner']['started_ns'])/1e6,
      'request_outstanding_ms':timing['time_partition']['request_outstanding_ms'],
      'presentation_callbacks_ms':timing['time_partition']['presentation_callbacks_ms'],
      'other_host_intervals_ms':timing['time_partition']['other_host_intervals_ms'],
      'cleanup_codes':{x['name']:x['returncode'] for x in d['cleanup']['children']}}
require(read(root/'manifest.json')['sha256']==sha(root/'runtime.pyz'),'archive hash')
for entry in read(root/'host'/'HOST_MANIFEST.json')['files']:
    require(entry['sha256']==sha(root/'host'/entry['path']),'host bundle hash')
results=[];mutations=[]
for arm,seed in [('full',1001080),('reuse',1001081)]:
    case=root/arm;rows=[json.loads(x) for x in (case/'primary-stream.jsonl').read_text().splitlines()]
    req={i:read(case/'exchange'/f'request-{i}.json') for i in range(1,14)}
    reply={i:read(case/'exchange'/f'original-reply-{i}.json') for i in (1,3,5,7,9,11,13)}
    meta={i:json.loads(next(b['text'] for b in r['result']['content'] if b['type']=='text')) for i,r in reply.items()}
    for i in range(1,14):require(rows[i]['result']==read(case/'exchange'/f'presentation-{i}.json'),'stream/file presentation differs')
    book=load_workbook(case/f'sheet-{seed}.xlsx',read_only=True,data_only=True)
    cells={c.coordinate:c.value for row in book.active for c in row if c.value is not None};book.close()
    d={'case':case,'reuse':arm=='reuse','rows':rows,'requests':req,'reply':reply,'meta':meta,
      'reviews':{i:read(case/'host'/f'review-{i}.json') for i in (1,3,4,5,6)},'cells':cells,
      'close_release':meta[13]['release'],'cleanup':read(case/'cleanup.json'),'score':read(case/'evaluation.json'),
      'owner':read(case/'owner.json'),'timing':read(root/f'{arm}-timing.json'),
      'events':[json.loads(x) for x in (case/'host'/'host-events.jsonl').read_text().splitlines()]}
    results.append(audit(d))
    for name in ('wrong-cell','stale-binding','missing-release')+ (('missing-reference',) if arm=='reuse' else ()):
        bad=copy.deepcopy(d)
        if name=='wrong-cell':bad['cells']['A1']=318
        elif name=='stale-binding':bad['requests'][11]['args'][1]['current_binding_revision']=1
        elif name=='missing-release':bad['meta'][5]['receipt']['execution_summary']['releases']=[]
        else:bad['rows'][7]['result']['presented_text']=[]
        try:audit(bad)
        except ValueError:mutations.append({'arm':arm,'mutation':name,'rejected':True})
        else:raise ValueError('missed mutation '+name)
print(json.dumps({'status':'PASS_LIVE_REUSE_ADMISSION_SCOPED','arms':results,'counterexamples':mutations,
 'efficiency_decision':'HOLD: one fixed-order known-family shared-context pair; no causal token/cost/tempo estimate'},indent=2))