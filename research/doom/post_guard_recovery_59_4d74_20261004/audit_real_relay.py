"""Independent of the runner's control flow: inspect retained bytes/joins only."""
from pathlib import Path
import json,hashlib,copy
root=Path(__file__).resolve().parent;out=root/'real-relay-construction-01'
def j(name):return json.loads((out/name).read_text())
requests=[json.loads(p.read_bytes()) for p in sorted(out.glob('request-*.jsonl'))]
paths=sorted(out.glob('response-*.jsonl'));responses=[json.loads(p.read_bytes()) for p in paths]
journal=[json.loads(x) for x in (out/'client-journal.jsonl').read_text().splitlines()]
result=j('RESULT.json');host=j('HOST.json');freeze=j('FREEZE.json')
def audit(rows,wire,req):
    e=[]
    def check(ok,label):
        if not ok:e.append(label)
    check(len(rows)==2,'two retained turns')
    check([m['method'] for m in req]==['initialize','initialized','thread/start',
                  'turn/start','turn/interrupt','turn/start'],'request order')
    if len(rows)!=2 or len(req)!=6:return e
    a,b=rows[0]['result'],rows[1]['result'];tid=a['handle']['thread_id']
    check(tid==b['handle']['thread_id'] and a['handle']['turn_id']!=b['handle']['turn_id'],
          'fresh distinct turn same thread')
    check(a['status']=='interrupted' and a['answer_eligible'] is False and a['answer'] is None
          and a['cancellation_requested'] is True and rows[0]['interrupt']['outcome']=='requested',
          'interrupted refusal')
    check(b['status']=='completed' and b['answer_eligible'] is True and
          b['cancellation_requested'] is False and b['answer']=={'marker':'recovery-relay-59-4d74'},
          'fresh exact eligible response')
    for row in rows:
        r=row['result'];turn=r['handle']['turn_id']
        started=[m for m in wire if m.get('method')=='turn/started' and
                 m['params']['threadId']==tid and m['params']['turn']['id']==turn]
        completed=[m for m in wire if m.get('method')=='turn/completed' and
                 m['params']['threadId']==tid and m['params']['turn']['id']==turn]
        check(len(started)==len(completed)==1,'turn lifecycle '+turn)
        if len(completed)==1:check(completed[0]['params']['turn']['status']==r['status'],'wire status '+turn)
        usage=[m['params']['tokenUsage'] for m in wire if m.get('method')=='thread/tokenUsage/updated' and
               m['params']['threadId']==tid and m['params']['turnId']==turn]
        check(r['usage']==(usage[-1] if usage else None),'usage exact or unavailable '+turn)
    interrupt=req[4];check(interrupt['params']=={'threadId':tid,'turnId':a['handle']['turn_id']},
                          'interrupt exact identity')
    for reqrow in (req[3],req[5]):
        check(reqrow['params']['threadId']==tid and reqrow['params']['model']=='gpt-5.6-luna'
              and reqrow['params']['effort']=='low','requested model identity')
    toolitems=[m for m in wire if m.get('method') in ('item/started','item/completed') and
               m.get('params',{}).get('item',{}).get('type') not in ('agentMessage','reasoning','userMessage')]
    check(not toolitems,'no observed tool items')
    return e
errors=audit(result['rows'],responses,requests)
if b''.join(p.read_bytes() for p in paths)!=(out/'host.stdout.jsonl').read_bytes():errors.append('host byte stream')
for direction,expected in [('sent',requests),('received',responses)]:
    if [m['message'] for m in journal if m['direction']==direction]!=expected:errors.append('client '+direction+' custody')
if host['container_exit']!=0 or host['host_exit']!=0 or host['reader_alive'] or host['error'] is not None:errors.append('owned terminal processes')
for name,digest in freeze['files'].items():
    p=Path(freeze['host_argv'][0]) if name=='CLI_SHA256' else root/name
    if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:errors.append('source identity '+name)
neg={}
bad=copy.deepcopy(result['rows']);bad[0]['result']['answer_eligible']=True
neg['stale_credited']=bool(audit(bad,responses,requests))
bad=copy.deepcopy(result['rows']);bad[1]['result']['handle']['turn_id']=bad[0]['result']['handle']['turn_id']
neg['old_turn_reused']=bool(audit(bad,responses,requests))
bad=copy.deepcopy(result['rows']);bad[0]['result']['usage']={'inputTokens':0}
neg['missing_usage_as_zero']=bool(audit(bad,responses,requests))
if not all(neg.values()):errors.append('negative control escaped')
r={'scope':'post-run raw-only single real protocol transport audit; no model cancellation latency guarantee/game recovery qualification',
   'errors':errors,'passed':not errors,'negative_controls':neg,'requested_turns':2,
   'first_turn_usage':'UNAVAILABLE','second_turn_usage':result['rows'][1]['result']['usage'],
   'whole_episode_token_cost':'UNKNOWN: interrupted turn has no attributable receipt'}
(out/'AUDIT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
raise SystemExit(bool(errors))
