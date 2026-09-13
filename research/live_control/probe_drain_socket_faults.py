"""Actual private Unix sockets: ready, stalled, trickled and broken drain replies."""
import hashlib,json,socket,tempfile,threading,time
from pathlib import Path
from drain_final import drain_final
from unix_json_deadline import exchange
HERE=Path(__file__).resolve().parent;out=HERE/'results/drain-socket-faults-01';out.mkdir(exist_ok=False)
source=HERE/'results/drain-calc-self-use-01/confirm/report.json';record=json.loads(source.read_text())
early=record['drain']['early'];final_reply=record['drain']['reply'];request_id=record['request_id'];rows=[]
for case in ('ready','stall','trickle','partial_close','malformed','oversized'):
    received=[];server_errors=[]
    with tempfile.TemporaryDirectory(prefix='agent-interface-drain-') as private:
        path=Path(private)/'test.sock'
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as server:
            server.bind(str(path));server.listen(1);server.settimeout(2)
            def serve():
                try:
                    connection,_=server.accept()
                    with connection:
                        connection.settimeout(2)
                        with connection.makefile('rb') as reader:received.append(json.loads(reader.readline()))
                        if case=='ready':connection.sendall((json.dumps(final_reply)+'\n').encode())
                        elif case=='stall':threading.Event().wait(.6)
                        elif case=='trickle':
                            for i in range(30):connection.sendall(b' ');threading.Event().wait(.03)
                        elif case=='partial_close':connection.sendall(b'{"status":')
                        elif case=='malformed':connection.sendall(b'not-json\n')
                        else:connection.sendall(b'x'*65+b'\n')
                except (BrokenPipeError,ConnectionResetError):pass
                except Exception as exc:server_errors.append(repr(exc))
            worker=threading.Thread(target=serve);worker.start();started=time.perf_counter_ns()
            result=drain_final(lambda request:exchange(path,request,timeout=.25,max_response_bytes=64 if case=='oversized' else 8*1024*1024),early,request_id,'confirm_excel')
            elapsed=(time.perf_counter_ns()-started)/1e6
            worker.join(timeout=2);assert not worker.is_alive() and not server_errors
            assert len(received)==1 and received[0]['timeout']==0 and 'command' not in received[0]
            if case=='ready':assert result['outcome']['state']=='evaluated' and result['outcome']['task_success'] is True
            else:
                assert result['outcome']==early and result['drain_state']=='transport_or_protocol_error'
                assert result['outcome']['task_success'] is None
            if case in ('stall','trickle'):assert 200<=elapsed<1000,(case,elapsed)
            rows.append(dict(case=case,elapsed_ms=elapsed,received=received,result=result))
(out/'results.json').write_text(json.dumps(rows,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),HERE/'drain_final.py',HERE/'unix_json_deadline.py',source)},indent=2)+'\n')
print(json.dumps([dict(case=r['case'],elapsed_ms=r['elapsed_ms'],state=r['result']['outcome']['state'],error=r['result'].get('error')) for r in rows],indent=2))
