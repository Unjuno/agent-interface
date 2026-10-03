"""One owned loopback fixture + one Node child; exclusive new output directory."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
from fixture import Fixture, serve

source = Path(__file__).resolve().parent
output = Path(sys.argv[1]).resolve()
mode = sys.argv[2] if len(sys.argv)>2 else 'formal'
output.mkdir(parents=True, exist_ok=False)
fixture = Fixture(json.loads((source/'fixtures.json').read_bytes()))
server, thread = serve(fixture)
origin = f'http://127.0.0.1:{server.server_port}'
command = [os.environ['STUDY_NODE'],str(source/'candidate.cjs'),origin,str(output/'client.json'),mode]
started = datetime.now(timezone.utc).isoformat()
result = None
try:
    with (output/'candidate.stdout').open('xb') as stdout, (output/'candidate.stderr').open('xb') as stderr:
        child = subprocess.Popen(command,stdout=stdout,stderr=stderr,env=os.environ.copy())
        # A live handle is retained for any timeout diagnosis; never restart the candidate.
        (output/'child.json').write_text(json.dumps({'pid':child.pid,'start_utc':started,'origin':origin})+'\n')
        try:
            result = child.wait(timeout=180)
        except subprocess.TimeoutExpired:
            (output/'TIMEOUT.json').write_text(json.dumps({'pid':child.pid,'state':'still_live_or_unknown','restart':False})+'\n')
            raise
finally:
    fixture.release.set()
    limit=time.monotonic()+3
    while fixture.active and time.monotonic()<limit:
        time.sleep(.01)
    server.shutdown();thread.join(timeout=2);server.server_close()
    ended=datetime.now(timezone.utc).isoformat()
    ledger={'schema':'6501-browser-server-v1','clock':'time.perf_counter_ns nanoseconds; server-only comparisons',
            'events':fixture.rows,'active_reads_at_close':fixture.active,'listener_closed':True,
            'thread_terminal':not thread.is_alive()}
    (output/'server.json').write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
    receipt={'command':['node','candidate.cjs','<owned-loopback-origin>','client.json',mode],
             'start_utc':started,'end_utc':ended,'exit_code':result,'source_sha256':
             {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir() if p.suffix in ('.cjs','.py') or p.name=='fixtures.json'},
             'clock_domains_not_merged':True,'resource_limits_not_enforced':True}
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'mode':mode,'exit_code':result,'server_active_reads':fixture.active,'server_thread_terminal':not thread.is_alive()}))
sys.exit(result if result is not None else 1)
