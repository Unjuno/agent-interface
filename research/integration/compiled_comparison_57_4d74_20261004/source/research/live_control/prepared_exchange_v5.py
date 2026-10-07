"""Explicit assistant program preparation and one send/wait exchange."""
import argparse,json,socket,time,uuid
from pathlib import Path
from prepare_program import prepare
from receipt_image import select_image
from outcome_wait import interpret
from drain_final import drain_final
from timing_clock import describe as describe_clock
from unix_json_deadline import exchange as bounded_exchange


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('socket');parser.add_argument('batch',type=Path);parser.add_argument('run_directory',type=Path)
    parser.add_argument('program_id');parser.add_argument('steps',type=Path)
    parser.add_argument('--lease-ms',type=int,required=True);parser.add_argument('--timeout',type=float,default=5)
    parser.add_argument('--boundary',choices=('terminal','outcome'),required=True)
    parser.add_argument('--producer',choices=('assistant','scripted','human'),default='assistant')
    parser.add_argument('--drain-final',action='store_true')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if not 0<=args.timeout<=30:raise ValueError('timeout 0..30 required')
    source=json.loads(args.batch.read_text());after=source.get('cursor')
    if type(after)is not int or after<0:raise ValueError('received cursor required')
    prepared=prepare(source,args.run_directory,args.program_id,json.loads(args.steps.read_text()),
        lease_ms=args.lease_ms,finish_after=args.boundary=='outcome')
    prepared['command']['decision_evidence']['producer']=args.producer
    identifier='program:'+uuid.uuid4().hex
    spec=dict(after=after,events=['terminal'] if args.boundary=='terminal' else ['effect_evidence','independent_evaluation'],
        timeout=args.timeout,command=prepared['command'],request_id=identifier,read_request_id=identifier)
    encoded=(json.dumps(spec,allow_nan=False)+'\n').encode()
    if len(encoded)>16384:raise ValueError('request exceeds socket line limit')
    args.out.mkdir(exist_ok=False)
    (args.out/'preparation.json').write_text(json.dumps(prepared,indent=2)+'\n')
    (args.out/'request.json').write_bytes(encoded)
    clock_identity=describe_clock()
    report=dict(request_id=identifier,program_id=args.program_id,clock=clock_identity,started_ns=time.perf_counter_ns(),authority='none')
    try:
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
            connection.settimeout(35);connection.connect(args.socket);connection.sendall(encoded)
            with connection.makefile('rb') as response:batch=json.loads(response.readline())
        report['returned_ns']=time.perf_counter_ns()
        (args.out/'reply.json').write_text(json.dumps(batch,indent=2)+'\n')
        report.update(status=batch['status'],cursor=batch.get('cursor'),command_receipt=batch.get('command_receipt'))
        if args.boundary=='outcome':report['outcome']=interpret(batch,identifier)
        # Image lookup failure must not erase a received action result.
        try:report['image']=select_image(batch,args.run_directory)
        except Exception as exc:report['image_error']=dict(type=type(exc).__name__,message=str(exc))
        report['records']=batch.get('records',[])
        if args.drain_final and args.boundary=='outcome':
            def read_tail(spec):
                (args.out/'drain-request.json').write_text(json.dumps(spec,indent=2)+'\n')
                tail=bounded_exchange(args.socket,spec,timeout=.25)
                (args.out/'drain-reply.json').write_text(json.dumps(tail,indent=2)+'\n')
                return tail
            report['drain']=drain_final(read_tail,report['outcome'],identifier,args.program_id)
            report['outcome']=report['drain']['outcome']
            if 'reply' in report['drain']:
                report['records']+=report['drain']['reply'].get('records',[])
                report['cursor']=report['drain']['reply'].get('cursor',report['cursor'])
        report['processing_finished_ns']=time.perf_counter_ns()
    except Exception as exc:
        report.update(status='transport_or_protocol_error',error=dict(type=type(exc).__name__,message=str(exc)),
            recovery='inspect persisted request; no automatic resend or new request ID')
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
