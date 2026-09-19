"""Build an explicit program using received evidence, without granting authority."""
import argparse,copy,json
from pathlib import Path
from receipt_image import select_image


def prepare(batch,run_directory,program_id,steps,*,lease_ms,finish_after=False):
    if not isinstance(program_id,str) or not 1<=len(program_id)<=128:raise ValueError('bounded program ID required')
    if type(lease_ms)is not int or not 1<=lease_ms<=30000:raise ValueError('lease_ms 1..30000 required')
    if type(finish_after)is not bool:raise ValueError('boolean finish_after required')
    if not isinstance(steps,list) or not steps:raise ValueError('explicit steps required')
    # Copy through strict JSON so caller mutation cannot change the prepared plan.
    steps=json.loads(json.dumps(steps,allow_nan=False))
    image=select_image(batch,run_directory)
    if image['status']!='image':raise ValueError('received image evidence required')
    sequence=image['sequence'];evidence=[];times=[]
    for record in batch['records']:
        event=record.get('event')
        if event=='observation' and record.get('sequence')==sequence:
            evidence.append(record.get('delivery_id'))
        elif event=='terminal':
            obs=record.get('review',{}).get('observation')
            if isinstance(obs,dict) and obs.get('sequence')==sequence:
                evidence.append(record.get('delivery_id'));times.append(record.get('terminal_ns'))
        elif event=='clock':
            if record.get('sequence')!=sequence:raise ValueError('clock observation differs from received image')
            times.append(record.get('runtime_ns'))
    if not evidence or any(not isinstance(v,str) or not v for v in evidence):raise ValueError('delivery reference required')
    if not times or any(type(v)is not int or v<=0 for v in times):raise ValueError('matching runtime timestamp required')
    base=max(times)
    command=dict(op='submit',id=program_id,expected_sequence=sequence,valid_until_ns=base+lease_ms*1_000_000,
        decision_evidence=dict(delivery_id=evidence[-1],observation_sequence=sequence,producer='assistant'),steps=steps)
    if finish_after:command['finish_after']=True
    return dict(command=command,image=image,source_clock_ns=base,lease_ms=lease_ms,
        authority='none; historical deadline, viewing and runtime admission remain required')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('batch',type=Path);parser.add_argument('run_directory',type=Path)
    parser.add_argument('program_id');parser.add_argument('steps',type=Path)
    parser.add_argument('--lease-ms',type=int,required=True);parser.add_argument('--finish-after',action='store_true')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=prepare(json.loads(args.batch.read_text()),args.run_directory,args.program_id,
        json.loads(args.steps.read_text()),lease_ms=args.lease_ms,finish_after=args.finish_after)
    with args.out.open('x') as output:output.write(json.dumps(result['command'],indent=2)+'\n')
    print(json.dumps(result))
