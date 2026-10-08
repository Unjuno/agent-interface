from pathlib import Path
import json,hashlib,copy
root=Path(__file__).resolve().parent;out=root/'image-relay-construction-01'
def load(name):return json.loads((out/name).read_text())
req=[json.loads(p.read_bytes()) for p in sorted(out.glob('request-*.jsonl'))]
paths=sorted(out.glob('response-*.jsonl'));wire=[json.loads(p.read_bytes()) for p in paths]
journal=[json.loads(x) for x in (out/'client-journal.jsonl').read_text().splitlines()]
result=load('RESULT.json');receipt=load('HOST_IMAGE_RECEIPT.json');host=load('HOST.json');freeze=load('FREEZE.json')
def audit(result,receipt,req,wire):
    e=[]
    def check(ok,name):
        if not ok:e.append(name)
    digest='70723e24d671fd656fa3ba40294b4cd28272493a9ffcacf93843cd86f13ab16d'
    check(result['source_sha256']==receipt['sha256']==digest,'image identity')
    check([x['method'] for x in req]==['initialize','initialized','thread/start','turn/start'],'one turn request')
    if len(req)!=4:return e
    inputs=req[3]['params']['input'];images=[x for x in inputs if x['type']=='localImage']
    check(len(images)==1 and images[0]['path']==receipt['submitted_path']==result['submitted_host_image'],
          'exact submitted path')
    prompts=[x['text'] for x in inputs if x['type']=='text']
    check(prompts==['Read the visible HEALTH and AMMO numbers in this screenshot.'],'fixed number-blind prompt')
    r=result['result'];t=r['handle']['turn_id'];thread=r['handle']['thread_id']
    check(r['status']=='completed' and r['answer_eligible'] is True and
          r['cancellation_requested'] is False and r['answer']=={'health':100,'ammo':48},'eligible exact answer')
    completions=[x for x in wire if x.get('method')=='turn/completed' and
                 x['params']['threadId']==thread and x['params']['turn']['id']==t]
    check(len(completions)==1 and completions[0]['params']['turn']['status']=='completed','terminal identity')
    if len(completions)==1:
        messages=[x for x in completions[0]['params']['turn']['items'] if x['type']=='agentMessage']
        check(len(messages)==1 and json.loads(messages[0]['text'])==r['answer'],'answer raw custody')
    usage=[x['params']['tokenUsage'] for x in wire if x.get('method')=='thread/tokenUsage/updated' and
           x['params']['threadId']==thread and x['params']['turnId']==t]
    check(bool(usage) and usage[-1]==r['usage'],'exact usage receipt')
    tools=[x for x in wire if x.get('method') in ('item/started','item/completed') and
           x.get('params',{}).get('item',{}).get('type') not in ('agentMessage','reasoning','userMessage')]
    check(not tools,'no observed tool item')
    check(req[3]['params']['model']=='gpt-5.6-luna' and req[3]['params']['effort']=='low','requested model')
    return e
errors=audit(result,receipt,req,wire)
if b''.join(p.read_bytes() for p in paths)!=(out/'host.stdout.jsonl').read_bytes():errors.append('host byte stream')
for direction,messages in [('sent',req),('received',wire)]:
    if [x['message'] for x in journal if x['direction']==direction]!=messages:errors.append('client '+direction+' custody')
for name,digest in freeze['files'].items():
    p=Path(freeze['host_argv'][0]) if name=='CLI_SHA256' else root/name
    if hashlib.sha256(p.read_bytes()).hexdigest()!=digest:errors.append('frozen source '+name)
if host['container_exit']!=0 or host['host_exit']!=0 or host['reader_alive'] or host['error'] is not None:errors.append('terminal processes')
neg={}
bad=copy.deepcopy(result);bad['source_sha256']='0'*64
neg['changed_source']=bool(audit(bad,receipt,req,wire))
bad=copy.deepcopy(result);bad['result']['answer']['ammo']=47
neg['wrong_read']=bool(audit(bad,receipt,req,wire))
bad=copy.deepcopy(result);bad['result']['answer_eligible']=False
neg['ineligible_credited']=bool(audit(bad,receipt,req,wire))
if not all(neg.values()):errors.append('negative control escaped')
r={'scope':'post-run single static image transport/read evidence; no provider decode receipt or live recovery proof',
   'errors':errors,'passed':not errors,'negative_controls':neg,'requested_turns':1,
   'usage':result['result']['usage']}
(out/'AUDIT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(bool(errors))
