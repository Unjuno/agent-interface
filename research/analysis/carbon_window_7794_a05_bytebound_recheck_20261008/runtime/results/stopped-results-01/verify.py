"""Finite audit of retained original artifacts; no new live invocation."""
from pathlib import Path
import json, hashlib, copy
base=Path(__file__).resolve().parent
case=base/'01-pending'
def read(p): return json.loads(p.read_text())
def check(ok,reason):
    if not ok: raise ValueError(reason)
def audit(rows,events,requests):
    check([r['request']['op'] for r in rows]==['observe','review','mint','input','review','results_after_stop','ack','observe_after_stop','review','close'],'primary command order')
    check([r['tool'] for r in requests]==['interface_guarded_observe','interface_guarded_mint','interface_guarded_input','interface_results','interface_guarded_observe','interface_close'],'public request order')
    initial,original,retrieved,later=rows[0],rows[3],rows[5],rows[7]
    check(requests[3]['arguments']=={'call_id':original['metadata']['call_id'],'include_image':False,'detail':'full'},'fixed historical request')
    check(all(r['caller_state']['stopped']=='unexpected MCP refusal' for r in rows[3:]),'sticky STOP')
    check(original['isError'] is True and original['metadata']['status']=='needs_review' and original['metadata']['result']['status']=='completed' and original['metadata']['feedback']['status']=='pending','original completed input pending cue')
    for key in ['call_id','operation','status','result','feedback','source','observation_report','session','replay_allowed','task_success']:
        check(retrieved['metadata'][key]==original['metadata'][key],'historical field '+key)
    check(retrieved['metadata']['operation_invoked'] is False,'retrieval invokes no operation')
    check(retrieved['image_path'] is None,'retrieval sends no image')
    check(events==[{'event':'save','token':'t1001071','ns':events[0]['ns']},{'event':'app_ack','status':'SAVED','ns':events[1]['ns']}],'exact once app effects')
    check(events[0]['ns']<events[1]['ns'],'app event ordering')
    check(original['metadata']['source']['capture_ns']<events[1]['ns']<later['metadata']['source']['capture_ns'],'capture acknowledgment ordering')
    check(later['metadata']['source']['sequence']==7 and retrieved['metadata']['source']['sequence']==6,'historical versus fresh source')
    check(later['metadata']['input_dispatched'] is False and later['metadata']['status']=='observed','later read-only observation')
    check(len({r['metadata']['session']['session_id'] for r in [initial,original,retrieved,later]})==1,'same session')

rows=[read(p) for p in sorted((case/'replies').glob('*.json'))]
events=[json.loads(line) for line in (case/'events.jsonl').read_text().splitlines()]
requests=[read(case/'host'/f'request-{i}.json') for i in range(1,7)]
check(read(case/'cleanup.json')['host_exit']==0 and read(case/'cleanup.json')['child_exit_codes']==[0,-15,0],'terminal owned processes')
check(read(case/'host-terminal.json')['exit']['code']==0,'host terminal')
audit(rows,events,requests)
for index,attempt in [(0,1),(2,2),(3,3),(5,4),(7,5),(9,6)]:
    raw=read(case/'host'/f'reply-{attempt}.json')['result']
    check(json.loads(next(b['text'] for b in raw['content'] if b['type']=='text'))==rows[index]['metadata'],'original host metadata')
    check(raw['isError']==rows[index]['isError'],'original framework error flag')
    if attempt==4: check(not any(b['type']=='image' for b in raw['content']),'no retrieval image content')
for index in [0,3,7]:
    row=rows[index];art=row['metadata']['source']['native']['artifact']
    original=Path(art['path']).read_bytes();primary=Path(row['image_path']).read_bytes()
    check(original==primary and hashlib.sha256(primary).hexdigest()==art['sha256'],'original primary PNG')
session=next((case/'calls').glob('guarded-session-*'))
check(len(list(session.glob('observation-*.json')))==7,'exact capture count')
check(len(list(session.glob('program-guarded-*.json')))==1,'one native input program')
check(len(list((case/'calls').glob('*/report.json')))==5,'retrieval creates no operation report')
mutations=[]
for name in ['clear_stop','alter_cue','alter_input','invoke_operation','send_image','extra_request','duplicate_save']:
    rr,ee,qq=copy.deepcopy((rows,events,requests))
    if name=='clear_stop': rr[5]['caller_state']['stopped']=None
    elif name=='alter_cue': rr[5]['metadata']['feedback']['status']='matched'
    elif name=='alter_input': rr[5]['metadata']['result']['status']='unknown'
    elif name=='invoke_operation': rr[5]['metadata']['operation_invoked']=True
    elif name=='send_image': rr[5]['image_path']='new.png'
    elif name=='extra_request': qq.append(copy.deepcopy(qq[2]))
    else: ee.append(copy.deepcopy(ee[0]))
    try: audit(rr,ee,qq)
    except (ValueError,KeyError): mutations.append(name)
    else: raise ValueError('counterexample accepted '+name)
report=dict(status='PASS',source_revision='5e503cdfc9e3a441cf330e840c35164f72f0a466',public_requests=6,primary_images=3,captures=7,native_programs=1,save_events=1,ack_events=1,stop_cleared=False,retrieval_added_images=0,retrieval_added_operation_reports=0,rejected_mutations=mutations,app_ack_delay_ms=(events[1]['ns']-events[0]['ns'])/1e6,later_capture_after_ack_ms=(rows[7]['metadata']['source']['capture_ns']-events[1]['ns'])/1e6,model_tokens=None,billing=None,comparative_efficiency='NOT_MEASURED')
(base/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
