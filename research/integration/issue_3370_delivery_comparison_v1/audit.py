"""Independent paired audit of direct and saved-file image delivery runs."""
import base64
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

root=Path(sys.argv[1])
failures=[]

def need(ok,label):
    if not ok:
        failures.append(label)

def read(folder,name):
    return json.loads((root/folder/name).read_text())

conditions=('direct_mcp_image','saved_file_view_image')
start_hashes=[]
decisions=[]
for condition in conditions:
    start=read(condition,'start.json')
    blocks=[b for b in start.get('content',[]) if b.get('type')=='image']
    image_path=root/condition/'start-image-1.png'
    need(len(blocks)==1,f'{condition}: one MCP start image')
    if blocks:
        raw=base64.b64decode(blocks[0]['data'],validate=True)
        image_hash=hashlib.sha256(raw).hexdigest()
        need(raw==image_path.read_bytes(),f'{condition}: exact MCP image bytes retained')
        need(image_hash==read(condition,'start-boundary.json')['image']['sha256'],
             f'{condition}: MCP image hash linked')
        start_hashes.append(image_hash)
    decision=read(condition,'decision.json')
    decisions.append(decision)
    need(decision.get('source_sequence')==1,f'{condition}: decision is source-bound')
    need(decision.get('finish_after') is True,f'{condition}: single submit is terminally bounded')
    client=read(condition,'client-result.json')
    need(client.get('status')=='returned',f'{condition}: client completed')
    need(client.get('submit_is_error') is False,f'{condition}: MCP submit transport passed')
    need(client.get('resume_count')==0,f'{condition}: no recovery resubmit')
    need(client.get('action_count')==1,f'{condition}: exactly one native input action')
    need('terminal' in client.get('status_polls',[]),f'{condition}: managed process terminal observed')
    response=read(condition,'submit.json')
    blocks=[b for b in response.get('content',[]) if b.get('type')=='image']
    need(len(blocks)==1,f'{condition}: one MCP feedback image retained')
    reply=read(condition,'allocation/run/reply-1.json')
    request_bytes=(root/condition/'allocation/run/request-1.json').read_bytes()
    need(reply.get('decision_sha256')==hashlib.sha256(request_bytes).hexdigest(),
         f'{condition}: immutable request/reply hash link')
    need(reply.get('status')=='finished',f'{condition}: task returned terminal finish')
    need(reply.get('evaluation',{}).get('success') is True,
         f'{condition}: independent saved-file task oracle passed')
    cleanup=reply.get('cleanup',{})
    need(cleanup.get('status')=='completed' and cleanup.get('tracked_processes_terminal') is True,
         f'{condition}: tracked cleanup completed')
    actions=read(condition,'allocation/run/actions.json')
    releases=actions[0].get('result',{}).get('execution',{}).get('releases',[]) if actions else []
    need(bool(releases) and all(r.get('verified') is True and r.get('keys_down')==[] and
         r.get('buttons_down')==[] for r in releases),f'{condition}: empty release independently verified')
    goal=read(condition,'allocation/run/goal.json')['task']
    svg=ET.parse(root/condition/'allocation/run/shape.svg')
    rects=[n for n in svg.iter() if n.tag.endswith('}rect')]
    need(len(rects)==1,f'{condition}: one scored rectangle')
    if rects:
        rect=rects[0]
        x,y,w,h=[float(rect.get(k)) for k in ('x','y','width','height')]
        need(x>goal['x_greater_than'] and abs(y-goal['y'])<goal['geometry_tolerance_exclusive']
             and abs(w-goal['width'])<goal['geometry_tolerance_exclusive']
             and abs(h-goal['height'])<goal['geometry_tolerance_exclusive']
             and rect.get('transform')==goal['transform'],f'{condition}: saved geometry matches task')
    terminal=read(condition,'status.json')
    meta=json.loads(terminal['content'][0]['text'])
    allocation=meta.get('allocation',{})
    need(allocation.get('status')=='terminal' and allocation.get('returncode')==0,
         f'{condition}: managed process exited zero')

need(len(start_hashes)==2 and start_hashes[0]==start_hashes[1],
     'paired initial MCP image bytes are identical')
need(len(decisions)==2 and decisions[0]==decisions[1],
     'paired model-authored decisions are identical')

result='PASS_BOTH_DELIVERY_PATHS_TASK_SCOPED' if not failures else 'FAIL_OR_HOLD'
audit={'schema':'agent-interface/issue-3370-delivery-pair-audit-v1','result':result,
       'conditions':list(conditions),'start_image_sha256':start_hashes,
       'failures':failures,'limits':['host presentation acknowledgement unavailable',
       'model-visible receipt/interpretation timestamps unavailable','provider token/cost unavailable',
       'n=1 per route; no latency or efficiency claim','no stale/delayed/no-image/disconnect controls']}
(root/'audit.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n')
print(json.dumps(audit,sort_keys=True))
raise SystemExit(0 if not failures else 1)
