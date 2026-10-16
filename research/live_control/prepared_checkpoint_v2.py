"""Explicit GUI program, checkpoint, and caller-selected conditional finish."""
import argparse,json,subprocess,sys,time,uuid
from pathlib import Path
from checkpoint_finish_v2 import run
from timing_clock import describe
from unix_json_deadline import exchange
HERE=Path(__file__).resolve().parent

def main():
    started=time.perf_counter_ns();clock=describe()
    parser=argparse.ArgumentParser()
    for name in ('socket','batch','run_directory','program_id','steps','contract'):parser.add_argument(name)
    parser.add_argument('--lease-ms',type=int,required=True)
    parser.add_argument('--finish-on-match',action='store_true',required=True)
    parser.add_argument('--producer',choices=('assistant','scripted','human'),default='assistant')
    parser.add_argument('--timeout',type=float,default=5)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if not 0<=args.timeout<=30:raise ValueError('timeout 0..30 required')
    contract=json.loads(Path(args.contract).read_text())
    # Validate the policy before issuing GUI input. The callback performs no I/O.
    run(lambda spec:dict(status='validation_only'),after=0,contract=contract,
        checkpoint_id='validate-checkpoint',finish_id='validate-finish',finish_on_match=True,timeout=args.timeout)
    args.out.mkdir(exist_ok=False)
    (args.out/'contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    result=dict(clock=clock,started_ns=started,authority='none',task_success=None)
    try:
        command=[sys.executable,str(HERE/'prepared_exchange_v6.py'),args.socket,args.batch,args.run_directory,args.program_id,args.steps,
            '--lease-ms',str(args.lease_ms),'--boundary','terminal','--producer',args.producer,'--timeout',str(args.timeout),'--out',str(args.out/'program')]
        process=subprocess.run(command,capture_output=True,text=True,timeout=40)
        (args.out/'program-stdout.json').write_text(process.stdout);(args.out/'program-stderr.txt').write_text(process.stderr)
        if process.returncode:raise RuntimeError('prepared caller failed; inspect persisted request before any replay')
        program=json.loads(process.stdout);result['program']=program;result['image']=program.get('image')
        records=program.get('records',[])
        if program.get('status')!='boundary' or not records or records[-1].get('event')!='terminal' or records[-1].get('status')!='completed':
            result['state']='program_unresolved'
        else:
            calls=[]
            def call(spec):
                record=dict(request=spec,started_ns=time.perf_counter_ns());calls.append(record)
                (args.out/f'policy-{len(calls)}-request.json').write_text(json.dumps(spec,indent=2)+'\n')
                try:record['reply']=exchange(args.socket,spec,timeout=args.timeout+1)
                finally:record['returned_ns']=time.perf_counter_ns()
                (args.out/f'policy-{len(calls)}-reply.json').write_text(json.dumps(record['reply'],indent=2)+'\n')
                return record['reply']
            result['policy']=run(call,after=program['cursor'],contract=contract,
                checkpoint_id='checkpoint:'+uuid.uuid4().hex,finish_id='finish:'+uuid.uuid4().hex,
                finish_on_match=args.finish_on_match,timeout=args.timeout)
            result['calls']=calls;result['state']=result['policy']['state'];result['task_success']=result['policy']['task_success']
            if result['policy'].get('continuation_allowed') is True:
                combined=list(records);cursor=program['cursor']
                for item in result['policy']['exchanges']:
                    reply=item['reply']
                    combined+=reply['records'];cursor=reply['cursor']
                (args.out/'continuation-batch.json').write_text(json.dumps(dict(records=combined,cursor=cursor),indent=2)+'\n')
    except Exception as exc:
        result.update(state='transport_or_protocol_error',error=dict(type=type(exc).__name__,message=str(exc)),recovery='inspect persisted requests; no automatic input replay')
    result['processing_finished_ns']=time.perf_counter_ns()
    (args.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':main()
