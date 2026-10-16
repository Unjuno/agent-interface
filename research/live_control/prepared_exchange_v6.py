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
    endpoints={'client_main_entered_ns':time.perf_counter_ns()}
    def mark(name):endpoints[name]=time.perf_counter_ns()
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
    mark('arguments_parsed_ns')
    source=json.loads(args.batch.read_text());after=source.get('cursor')
    mark('source_loaded_ns')
    if type(after)is not int or after<0:raise ValueError('received cursor required')
    prepared=prepare(source,args.run_directory,args.program_id,json.loads(args.steps.read_text()),
        lease_ms=args.lease_ms,finish_after=args.boundary=='outcome')
    mark('program_prepared_ns')
    prepared['command']['decision_evidence']['producer']=args.producer
    identifier='program:'+uuid.uuid4().hex
    spec=dict(after=after,events=['terminal'] if args.boundary=='terminal' else ['effect_evidence','independent_evaluation'],
        timeout=args.timeout,command=prepared['command'],request_id=identifier,read_request_id=identifier)
    encoded=(json.dumps(spec,allow_nan=False)+'\n').encode()
    if len(encoded)>16384:raise ValueError('request exceeds socket line limit')
    args.out.mkdir(exist_ok=False)
    (args.out/'preparation.json').write_text(json.dumps(prepared,indent=2)+'\n')
    (args.out/'request.json').write_bytes(encoded)
    mark('request_persisted_ns')
    clock_identity=describe_clock()
    mark('clock_described_ns')
    report=dict(request_id=identifier,program_id=args.program_id,clock=clock_identity,endpoints=endpoints,started_ns=time.perf_counter_ns(),authority='none')
    try:
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
            connection.settimeout(35);connection.connect(args.socket)
            mark('socket_connected_ns')
            connection.sendall(encoded)
            mark('request_sendall_returned_ns')
            with connection.makefile('rb') as response:
                raw=response.readline()
                mark('response_line_received_ns')
                batch=json.loads(raw)
                mark('response_decoded_ns')
        report['returned_ns']=time.perf_counter_ns()
        (args.out/'reply.json').write_text(json.dumps(batch,indent=2)+'\n')
        report.update(status=batch['status'],cursor=batch.get('cursor'),command_receipt=batch.get('command_receipt'))
        if args.boundary=='outcome':report['outcome']=interpret(batch,identifier)
        # Image lookup failure must not erase a received action result.
        try:report['image']=select_image(batch,args.run_directory)
        except Exception as exc:report['image_error']=dict(type=type(exc).__name__,message=str(exc))
        mark('result_and_image_processed_ns')
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
        mark('optional_drain_finished_ns')
        report['processing_finished_ns']=time.perf_counter_ns()
    except Exception as exc:
        report.update(status='transport_or_protocol_error',error=dict(type=type(exc).__name__,message=str(exc)),
            recovery='inspect persisted request; no automatic resend or new request ID')
    report['unobserved_endpoints']={name:None for name in (
        'model_observation_received_ns','model_generation_started_ns',
        'model_generation_finished_ns','model_result_received_ns')}
    report['timing_scope']='client-local marks; sendall is not runtime admission; line receipt is not model receipt; endpoints absent on unfinished phases'
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    mark('report_file_written_ns')
    output=json.dumps(report)
    mark('stdout_serialized_ns')
    print(output,flush=True)
    mark('stdout_flush_returned_ns')
    # These later marks cannot appear in the already serialized response.
    (args.out/'client-endpoints.json').write_text(json.dumps(dict(
        clock=clock_identity,endpoints=endpoints,unobserved_endpoints=report['unobserved_endpoints'],
        scope='flush return is local pipe completion, not consumer or model receipt'),indent=2)+'\n')


if __name__=='__main__':main()
