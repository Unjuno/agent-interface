"""One outer call: explicit clock query then explicit v9 program; no input retry."""
import argparse
import json
from pathlib import Path
import time
import uuid
from receipt_image import select_image
from stopped_client_v1 import PendingAction
from unix_json_deadline import exchange

def prefix(reply,after):
    if not isinstance(reply,dict) or not isinstance(reply.get('records'),list):raise ValueError('records required')
    if type(reply.get('cursor')) is not int or reply['cursor']!=after+len(reply['records']):raise ValueError('noncontiguous reply')
    if reply.get('status')!='boundary':raise ValueError('boundary unresolved: '+str(reply.get('status')))
    return reply['records']

def own_command(records,identifier,op):
    matches=[i for i,r in enumerate(records) if r.get('event')=='command'
             and r.get('command',{}).get('transport_request_id')==identifier
             and r['command'].get('op')==op]
    if len(matches)!=1:raise ValueError('own command echo required')
    return matches[0]

def run(query,batch,root,program_id,steps,lease_ms,persist):
    result={'state':'needs_reconciliation','exchanges':[],'program_sent':False}
    def call(request):
        record={'request':request,'started_ns':time.perf_counter_ns()};result['exchanges'].append(record)
        persist('request-'+str(len(result['exchanges'])),request)
        reply=query(request);record['returned_ns']=time.perf_counter_ns();record['reply']=reply
        persist('reply-'+str(len(result['exchanges'])),reply)
        return reply
    try:
        if type(batch.get('cursor')) is not int or batch['cursor']<0:raise ValueError('received cursor required')
        if not isinstance(program_id,str) or not 1<=len(program_id)<=128:raise ValueError('bounded program id required')
        if type(lease_ms) is not int or not 1<=lease_ms<=30000:raise ValueError('lease 1..30000ms required')
        if not isinstance(steps,list) or not steps:raise ValueError('explicit steps required')
        steps=json.loads(json.dumps(steps,allow_nan=False))
        observed=select_image(batch,root)
        if observed['status']!='image':raise ValueError('received image required')
        result['source_image']=observed
        clock_id='clock-'+uuid.uuid4().hex
        clock=call({'after':batch['cursor'],'events':['clock'],'timeout':5,
                    'request_id':clock_id,'command':{'op':'clock'}})
        records=prefix(clock,batch['cursor']);index=own_command(records,clock_id,'clock')
        if not records or records[-1].get('event')!='clock':raise ValueError('clock boundary required')
        if any(r.get('event')=='command' for r in records[index+1:]):raise ValueError('interleaved clock command')
        now=records[-1]
        if now.get('sequence')!=observed['sequence'] or type(now.get('runtime_ns')) is not int or now['runtime_ns']<=0:
            raise ValueError('clock sequence or timestamp mismatch; no new image authority')
        request_id='program-'+uuid.uuid4().hex
        command={'op':'submit','id':program_id,'steps':steps,'expected_sequence':observed['sequence'],
                 'valid_until_ns':now['runtime_ns']+lease_ms*1000000}
        result['program_sent']=True # means write may be attempted, not runtime admission
        reply=call({'after':clock['cursor'],'events':['input_stopped','terminal'],'timeout':15,'action_id':program_id,
                    'request_id':request_id,'command':command})
        result['last_reply']=reply
        records=prefix(reply,clock['cursor']);index=own_command(records,request_id,'submit')
        terminal=records[-1]
        if terminal.get('event') not in ('input_stopped','terminal') or terminal.get('id')!=program_id or index>=len(records)-1:
            raise ValueError('own terminal required')
        if not any(r.get('event')=='accepted' and r.get('id')==program_id for r in records[index+1:]):
            raise ValueError('own admission required')
        tracker=PendingAction(program_id,clock['cursor'])
        lifecycle=tracker.ingest(clock['cursor'],reply)
        result.update(state=lifecycle['state'],lifecycle=lifecycle,image=select_image(reply,root))
        if terminal['event']=='terminal':result['terminal']=terminal
        result['continuation_batch']=reply
    except Exception as exc:
        result['reason']=str(exc)
    result['authority']='none; clock refresh does not refresh image; ordinary v9 admission applies'
    return result

def main():
    ap=argparse.ArgumentParser()
    for name in ('socket','batch','run_directory','program_id','steps'):ap.add_argument(name)
    ap.add_argument('--lease-ms',type=int,default=30000);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    def persist(name,value):(a.out/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')
    batch=json.loads(Path(a.batch).read_text());steps=json.loads(Path(a.steps).read_text())
    persist('source-batch',batch);persist('steps',steps)
    result=run(lambda spec:exchange(a.socket,spec,timeout=16),batch,a.run_directory,a.program_id,steps,a.lease_ms,persist)
    persist('report',result);print(json.dumps(result),flush=True)

if __name__=='__main__':main()
