"""Real AF_UNIX peer that accepts a read but sends no response before the deadline."""
import json
import socket
import tempfile
import threading
import time
from pathlib import Path
from bounded_followup_v2 import collect
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent;root=HERE/'results/followup-io-01';root.mkdir(exist_ok=False)
source=HERE/'results/bounded-followup-02/pending-report.json'
previous=json.loads(source.read_text());received=[]
with tempfile.TemporaryDirectory(prefix='agent-interface-followup-') as private:
    path=str(Path(private)/'events.sock');release=threading.Event()
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as server:
        server.bind(path);server.listen(1);server.settimeout(2)
        def peer():
            with server.accept()[0] as client:
                client.settimeout(2)
                with client.makefile('rb') as stream:received.append(json.loads(stream.readline()))
                release.wait(2)
        thread=threading.Thread(target=peer);thread.start()
        try:
            start=time.perf_counter_ns();result=collect(path,previous,root);elapsed=(time.perf_counter_ns()-start)/1e6
            assert result['state']=='input_stopped_capture_pending'
            assert result['lifecycle']['cursor']==previous['lifecycle']['cursor']
            assert result['bounded_followup']['read_error']['type']=='TimeoutError'
            assert 500<elapsed<1200
            assert len(received)==1 and 'command' not in received[0]
        finally:release.set();thread.join(3);assert not thread.is_alive()
report=dict(success=True,elapsed_ms=elapsed,received=received,result=result,
    source_sha256=digest(source.read_bytes()),sources={n:digest((HERE/n).read_bytes()) for n in
    ['probe_followup_io_v1.py','bounded_followup_v2.py','unix_json_deadline.py']},
    scope='One real socket response stall; socket I/O deadline excludes report processing and image file operations')
(root/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(success=True,elapsed_ms=elapsed,cursor_preserved=True)))
