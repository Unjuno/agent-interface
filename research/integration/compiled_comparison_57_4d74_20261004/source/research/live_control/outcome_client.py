"""One bounded caller invocation over an existing private Unix socket."""
import argparse,json,socket,time
from pathlib import Path
from outcome_fallback_v2 import wait_with_status


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('socket');parser.add_argument('request_id');parser.add_argument('program_id')
    parser.add_argument('--after',type=int,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--timeout',type=float,default=1);parser.add_argument('--status-timeout',type=float,default=1)
    parser.add_argument('--final-only',action='store_true')
    args=parser.parse_args()
    # Reserve output before making a query, so an accidental overwrite does not
    # perform network work. The transcript is local evidence, not a durable ACK.
    with args.out.open('x') as output:
        def exchange(spec):
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
                connection.settimeout(35);connection.connect(args.socket)
                connection.sendall((json.dumps(spec)+'\n').encode())
                with connection.makefile('rb') as stream:return json.loads(stream.readline())
        started=time.perf_counter_ns()
        result=wait_with_status(exchange,args.request_id,args.program_id,args.after,
            timeout=args.timeout,status_timeout=args.status_timeout,final_only=args.final_only)
        result.update(client_started_ns=started,client_returned_ns=time.perf_counter_ns())
        output.write(json.dumps(result,indent=2)+'\n');output.flush()
    print(json.dumps(dict(result=result['result'],exchange_calls=len(result['transcript']),
        client_started_ns=result['client_started_ns'],client_returned_ns=result['client_returned_ns'])))


if __name__=='__main__':main()
