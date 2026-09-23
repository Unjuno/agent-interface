"""Private Linux observation socket around an unchanged interactive subprocess.

Input remains the inherited stdin lane. Socket requests cannot submit actions.
"""
import argparse,json,socket,socketserver,subprocess,sys,tempfile,threading
from pathlib import Path
from event_cursor import EventCursor


def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='mode',required=True)
    serve=sub.add_parser('serve');serve.add_argument('runtime_args',nargs=argparse.REMAINDER)
    read=sub.add_parser('read');read.add_argument('socket');read.add_argument('--after',type=int,default=0)
    read.add_argument('--until',nargs='+',required=True);read.add_argument('--timeout',type=float,default=5)
    args=ap.parse_args()
    if args.mode=='read':
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
            connection.settimeout(35);connection.connect(args.socket)
            connection.sendall((json.dumps(dict(after=args.after,events=args.until,timeout=args.timeout))+'\n').encode())
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
                if not isinstance(command,dict) or set(command)!={'after','events','timeout'}:raise ValueError('read fields only')
                result=cursor.read_until(**command)
            except Exception as exc:result=dict(status='error',error=type(exc).__name__,message=str(exc))
            try:self.wfile.write((json.dumps(result)+'\n').encode());self.wfile.flush()
            except (BrokenPipeError,ConnectionResetError,TimeoutError):pass
    with tempfile.TemporaryDirectory(prefix='agent-interface-events-') as private:
        # mkdtemp creates mode 0700; no TCP listener or public command endpoint.
        socket_path=Path(private)/'events.sock'
        with socketserver.UnixStreamServer(str(socket_path),Handler) as server:
            server_thread=threading.Thread(target=server.serve_forever,daemon=True);server_thread.start()
            runtime_args=args.runtime_args
            if runtime_args[:1]==['--']:runtime_args=runtime_args[1:]
            process=subprocess.Popen([sys.executable,'-u',str(Path(__file__).with_name('interactive_v23.py')),*runtime_args],stdout=subprocess.PIPE,text=True)
            def consume():
                try:
                    for line in process.stdout:cursor.append(json.loads(line))
                except Exception as exc:failures.append(repr(exc))
                finally:cursor.close()
            reader=threading.Thread(target=consume,daemon=True);reader.start()
            print(json.dumps(dict(event='observation_socket',socket=str(socket_path),input='inherited stdin; ordinary runtime admission',authority='socket is read-only')),flush=True)
            try:code=process.wait();reader.join()
            finally:
                server.shutdown();server_thread.join();cursor.close()
            if failures:raise RuntimeError(failures)
            if code:raise SystemExit(code)


if __name__=='__main__':main()
