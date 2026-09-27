"""Private Linux send-and-wait candidate around an unchanged interactive subprocess.

Commands forward unchanged with a session-local at-most-one write attempt.
"""
import argparse,json,os,socket,socketserver,subprocess,sys,tempfile,threading,time
from pathlib import Path
from event_cursor_v5 import EventCursor
from command_once_v2 import CommandOnce
from bounded_pipe_writer_v2 import BoundedPipeWriter


class BoundedServer(socketserver.ThreadingMixIn,socketserver.UnixStreamServer):
    daemon_threads=True
    def __init__(self,*args,**kwargs):
        self.slots=threading.BoundedSemaphore(8)
        super().__init__(*args,**kwargs)
    def process_request(self,request,client_address):
        if not self.slots.acquire(blocking=False):
            try:
                request.settimeout(.1)
                request.sendall(b'{"status":"busy","command_forwarded":false}\n')
            except OSError:pass
            finally:self.shutdown_request(request)
            return
        try:super().process_request(request,client_address)
        except Exception:
            self.slots.release();raise
    def process_request_thread(self,request,client_address):
        try:super().process_request_thread(request,client_address)
        finally:self.slots.release()


def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='mode',required=True)
    serve=sub.add_parser('serve');serve.add_argument('runtime_args',nargs=argparse.REMAINDER)
    read=sub.add_parser('read');read.add_argument('socket');read.add_argument('--after',type=int,default=0)
    read.add_argument('--until',nargs='+',required=True);read.add_argument('--timeout',type=float,default=5)
    read.add_argument('--read-request-id');read.add_argument('--action-id');read.add_argument('--command-file',type=Path);read.add_argument('--request-id')
    args=ap.parse_args()
    if args.mode=='read':
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
            connection.settimeout(35);connection.connect(args.socket)
            request=dict(after=args.after,events=args.until,timeout=args.timeout)
            if args.read_request_id is not None:request['read_request_id']=args.read_request_id
            if args.action_id is not None:request['action_id']=args.action_id
            if args.command_file is not None:request.update(request_id=args.request_id,command=json.loads(args.command_file.read_text()))
            connection.sendall((json.dumps(request)+'\n').encode())
            with connection.makefile('rb') as response:print(response.readline().decode().strip(),flush=True)
        return
    cursor=EventCursor();failures=[]
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.connection.settimeout(2)
            try:
                line=self.rfile.readline(16385)
                if len(line)>16384 or not line.endswith(b'\n'):raise ValueError('bounded JSON line required')
                command=json.loads(line)
                if not isinstance(command,dict) or (set(command)-{'action_id','read_request_id'}) not in ({'after','events','timeout'},{'after','events','timeout','command','request_id'}):raise ValueError('invalid request fields')
                if getattr(self.server,'cancel_lane',False):
                    if command.get('command',{}).get('op')!='cancel':raise ValueError('cancel lane accepts cancel only')
                    if type(command['timeout']) not in (int,float) or not 0<=command['timeout']<=1:raise ValueError('cancel lane wait at most one second')
                read_args={k:command[k] for k in ('after','events','timeout')}
                if 'read_request_id' in command:read_args['request_id']=command['read_request_id']
                if 'action_id' in command:
                    read_args['action_id']=command['action_id']
                    submitted=command.get('command',{})
                    if submitted.get('op') in ('submit','cancel') and submitted.get('id')!=command['action_id']:raise ValueError('command/action scope mismatch')
                # Validate full read request before any command write.
                probe=cursor.read_until(**dict(read_args,timeout=0))
                if type(read_args['timeout']) not in (int,float) or not 0<=read_args['timeout']<=30:raise ValueError('timeout 0..30 required')
                if probe['status']=='gap':result=probe
                else:
                    receipt=None
                    if 'command' in command:
                        if not isinstance(command['command'],dict) or 'transport_request_id' in command['command']:raise ValueError('reserved transport identity field')
                        forwarded=dict(command['command'],transport_request_id=command['request_id'])
                        receipt=sender.send(command['request_id'],forwarded)
                    if receipt is not None and receipt['state']!='stdin_flushed':
                        result=dict(status=receipt['state'],records=[],cursor=read_args['after'],recovery='inspect command receipt; no automatic resend; observation grants no authority')
                    else:result=cursor.read_until(**read_args)
                    if receipt is not None:result['command_receipt']=receipt
            except Exception as exc:result=dict(status='error',error=type(exc).__name__,message=str(exc))
            try:self.wfile.write((json.dumps(result)+'\n').encode());self.wfile.flush()
            except (BrokenPipeError,ConnectionResetError,TimeoutError):pass
    with tempfile.TemporaryDirectory(prefix='agent-interface-events-') as private:
        # mkdtemp creates mode 0700; no TCP listener; same-user private command endpoint.
        socket_path=Path(private)/'events.sock'
        with BoundedServer(str(socket_path),Handler) as server:
            server_thread=threading.Thread(target=server.serve_forever,daemon=True)
            runtime_args=args.runtime_args
            if runtime_args[:1]==['--']:runtime_args=runtime_args[1:]
            process=subprocess.Popen([sys.executable,'-u',str(Path(__file__).with_name('interactive_v27.py')),*runtime_args],stdin=subprocess.PIPE,stdout=subprocess.PIPE,bufsize=0)
            pipe_writer=BoundedPipeWriter(process.stdin.fileno())
            def write(line):
                try:pipe_writer(line)
                except Exception:
                    if pipe_writer.poisoned:process.stdin.close()
                    raise
            sender=CommandOnce(write);server_thread.start()
            cancel_path=Path(private)/'cancel.sock'
            cancel_server=BoundedServer(str(cancel_path),Handler);cancel_server.cancel_lane=True
            cancel_server.slots=threading.BoundedSemaphore(2)
            cancel_thread=threading.Thread(target=cancel_server.serve_forever,daemon=True);cancel_thread.start()
            runtime_ready=threading.Event();ready_trace={}
            def consume():
                try:
                    for line in process.stdout:
                        record=json.loads(line);cursor.append(record)
                        if (record.get('event')=='ready' and
                            record.get('decision_evidence_schema',{}).get('authority')=='none; ordinary admission required'):
                            ready_trace['ready_append_ns']=time.perf_counter_ns();runtime_ready.set()
                except Exception as exc:failures.append(repr(exc))
                finally:cursor.close()
            reader=threading.Thread(target=consume,daemon=True);reader.start()
            if not runtime_ready.wait(5):
                process.terminate();process.wait(timeout=2);reader.join(timeout=2)
                raise RuntimeError('existing runtime ready event not observed')
            ready_trace['endpoint_publish_ns']=time.perf_counter_ns()
            trace_path=os.environ.get('AI_EXISTING_READY_TRACE')
            if trace_path:Path(trace_path).write_text(json.dumps(ready_trace,sort_keys=True)+'\n')
            print(json.dumps(dict(event='observation_socket',socket=str(socket_path),cancel_socket=str(cancel_path),input='optional once-only command forwarding; ordinary runtime admission',authority='no lease renewal; session-local deduplication')),flush=True)
            try:code=process.wait();reader.join()
            finally:
                cancel_server.shutdown();cancel_thread.join();cancel_server.server_close()
                server.shutdown();server_thread.join();cursor.close()
            if failures:raise RuntimeError(failures)
            if code:raise SystemExit(code)


if __name__=='__main__':main()
