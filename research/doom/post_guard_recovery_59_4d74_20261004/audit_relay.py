"""Post-run raw-only transport auditor; never invokes a peer/provider."""
from pathlib import Path
import json,hashlib,sys,copy
root=Path(__file__).resolve().parent;out=root/'relay-construction-02'
def read(name):return json.loads((out/name).read_text())
def audit(result,responses,requests,journal,host):
    errors=[]
    def check(ok,label):
        if not ok:errors.append(label)
    check(host['container_exit']==0 and host['host_exit']==0 and
          host['reader_alive'] is False and host['error'] is None,'terminal processes')
    check(host['provider_calls']==host['game_sessions']==host['input_emissions']==0,'scope counters')
    check(len(requests)==host['requests_forwarded']==8,'request cardinality')
    check(len(responses)==host['responses_forwarded']==13,'response cardinality')
    check([r['message'] for r in journal if r['direction']=='sent']==requests,'client send custody')
    check([r['message'] for r in journal if r['direction']=='received']==responses,'client receive custody')
    methods=[r['method'] for r in requests]
    check(methods==['initialize','initialized','thread/start','turn/start','turn/interrupt',
                    'turn/start','turn/interrupt','turn/start'],'protocol order')
    expected=['fake-turn-1','fake-turn-2','fake-turn-3']
    rows=result['rows'];check(len(rows)==3,'case cardinality')
    if len(rows)!=3:return errors
    for index,(row,turn) in enumerate(zip(rows,expected)):
        r=row['result'];check(r['handle']['thread_id']=='fake-thread' and
              r['handle']['turn_id']==turn,'turn identity '+turn)
        completions=[m for m in responses if m.get('method')=='turn/completed' and
            m['params']['turn']['id']==turn]
        check(len(completions)==1 and completions[0]['params']['turn']['status']==r['status'],
              'completion status '+turn)
        if index<2:
            check(r['answer_eligible'] is False and r['cancellation_requested'] is True and
                  r['answer'] is None and row['interrupt']['outcome']=='requested','stale refusal '+turn)
            interrupts=[m for m in requests if m['method']=='turn/interrupt' and m['params']['turnId']==turn]
            check(len(interrupts)==1,'interrupt identity '+turn)
        else:
            check(r['answer_eligible'] is True and r['cancellation_requested'] is False and
                  r['answer']=={'action':'fresh'},'fresh continuation')
        check(r['usage'] is None,'fake usage unavailable '+turn)
    check(rows[0]['result']['status']=='interrupted','first interrupted')
    check(rows[1]['result']['status']=='completed','second completed but invalidated')
    check(result['reader_alive'] is False and result['proxy_exit'] is not None,'proxy terminal')
    return errors

result=read('RESULT.json');host=read('HOST.json')
requests=[json.loads(p.read_bytes()) for p in sorted(out.glob('request-*.jsonl'))]
paths=sorted(out.glob('response-*.jsonl'));responses=[json.loads(p.read_bytes()) for p in paths]
journal=[json.loads(x) for x in (out/'client-journal.jsonl').read_text().splitlines()]
errors=audit(result,responses,requests,journal,host)
if b''.join(p.read_bytes() for p in paths)!=(out/'host.stdout.jsonl').read_bytes():
    errors.append('host response byte stream')
f=read('FREEZE.json')
for name,h in f['files'].items():
    if hashlib.sha256((root/name).read_bytes()).hexdigest()!=h:errors.append('frozen source '+name)
mutations={}
bad=copy.deepcopy(result);bad['rows'][1]['result']['answer_eligible']=True
mutations['stale_answer_credited']=bool(audit(bad,responses,requests,journal,host))
bad=copy.deepcopy(result);bad['rows'][2]['result']['handle']['turn_id']='fake-turn-1'
mutations['old_turn_reused']=bool(audit(bad,responses,requests,journal,host))
bad=copy.deepcopy(responses);bad[-1]['params']['turn']['status']='interrupted'
mutations['completion_status_corrupt']=bool(audit(result,bad,requests,journal,host))
mutations['lost_response']=bool(audit(result,responses[:-1],requests,journal,host))
if not all(mutations.values()):errors.append('negative control escaped')
r={'scope':'post-run raw-only finite fake-peer setup audit; no real model/interrupt/game/physical input qualification',
   'errors':errors,'passed':not errors,'negative_controls':mutations}
(out/'AUDIT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
raise SystemExit(bool(errors))
