"""Startup ownership regression: inert dependencies and real owned stdlib children."""
import ast,atexit,contextlib,hashlib,json,os,subprocess,sys,tempfile,threading,time,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'map01_overlap_controller_v39.py'
OUTPUT=os.environ.get('AGENT_INTERFACE_STARTUP_TEST_OUTPUT')
def child(mode,trace):
    def record(name,**extra):
        with Path(trace).open('a',encoding='utf-8') as f:
            f.write(json.dumps(dict(event=name,pid=os.getpid(),ns=time.perf_counter_ns(),**extra))+'\n')
    record('started')
    print(json.dumps(dict(event='ready',fixture={} if mode=='normal' else None)),flush=True)
    print(json.dumps(dict(event='observation',sequence=1,capture_to_artifact_ready_ms=0)),flush=True)
    if mode=='stderr-overflow':
        sys.stderr.buffer.write(b'x'*65537);sys.stderr.buffer.flush();record('stderr_sent')
    for line in sys.stdin:
        command=json.loads(line);record('command',command=command)
        if command.get('op')=='finish':
            print(json.dumps(dict(event='post_control_score',outcome='inert_fixture')),flush=True)
            record('closed');return
    record('eof')
    if mode=='noncooperative':
        while True:time.sleep(1)
    record('closed')
@contextlib.contextmanager
def fixture(name,mode='cooperative',fault=None,close_fault=False):
    temp=None
    if OUTPUT:
        out=Path(OUTPUT)/name;out.mkdir(parents=True,exist_ok=False)
    else:
        temp=tempfile.TemporaryDirectory(prefix='v39-startup-');out=Path(temp.name)
    owned=[];readers=[];clients=[];calls=[]
    def unexpected(*a,**kw):raise RuntimeError('out-of-scope model/input boundary')
    class Client:
        def __init__(self,*a,**kw):self.closes=0;clients.append(self);calls.append('client_acquired')
        def initialize(self):
            calls.append('initialize')
            if fault=='initialize':raise ValueError('injected initialize error')
        def close(self,timeout=5):
            self.closes+=1;calls.append('client_close')
            if close_fault:raise RuntimeError('injected client cleanup error')
    class Planner:
        def __init__(self,*a,**kw):self.thread_id='inert'
        def start_session(self):calls.append('planner_start')
    class NumberReader:
        def __init__(self,*a,**kw):pass
        def read(self,*a,**kw):return unexpected()
    fake={}
    standard={'argparse','atexit','collections','concurrent.futures','hashlib','json','queue','subprocess','sys','threading','time','pathlib'}
    for n in ast.parse(SOURCE.read_bytes()).body:
        if not isinstance(n,ast.ImportFrom) or n.module in standard:continue
        module=types.ModuleType(n.module)
        for item in n.names:
            value={'CodexAppServerClient':Client,'PersistentPlannerAdapter':Planner,'DoomStatusNumberReader':NumberReader}.get(item.name,unexpected)
            if item.name.isupper():value='inert_'+item.name
            setattr(module,item.name,value)
        fake[n.module]=module
    subject=types.ModuleType('startup_subject');subject.__file__=str(SOURCE)
    trace=out/'child-events.jsonl'
    with patch.dict(sys.modules,fake), patch.object(sys,'path',list(sys.path)):
        exec(compile(SOURCE.read_bytes(),str(SOURCE),'exec'),subject.__dict__)
    def spawn(_argv,**kw):
        if fault=='spawn':raise OSError('injected session spawn error')
        p=subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--child',mode,str(trace)],**kw)
        owned.append(p);calls.append('session_acquired');return p
    def thread(*a,**kw):
        if fault=='reader_start' and not readers:
            class Unstarted:
                ident=None
                def start(self):raise RuntimeError('injected stdout reader start error')
                def is_alive(self):return False
                def join(self,timeout=None):raise RuntimeError('unstarted thread was joined')
            t=Unstarted()
        else:t=threading.Thread(*a,**kw)
        readers.append(t);return t
    subject.subprocess=types.SimpleNamespace(Popen=spawn,PIPE=subprocess.PIPE,TimeoutExpired=subprocess.TimeoutExpired)
    subject.threading=types.SimpleNamespace(Thread=thread)
    subject.win=lambda p:str(p)
    argv=['startup-subject','--out',str(out/'controller'),'--iterations','0','--model','not-invoked','--effort','low','--load-fixture-manifest',str(out/'unused.json')]
    state=dict(subject=subject,owned=owned,readers=readers,clients=clients,calls=calls,out=out,trace=trace)
    start=time.perf_counter_ns()
    try:
        with patch.object(sys,'argv',argv):yield state
    finally:
        before=dict(process_poll=[p.poll() for p in owned],reader_alive=[t.is_alive() for t in readers],client_closes=[c.closes for c in clients],calls=list(calls),observed_ns=time.perf_counter_ns())
        for p in owned:
            if p.stdin and not p.stdin.closed:p.stdin.close()
            try:p.wait(timeout=1)
            except subprocess.TimeoutExpired:
                p.terminate()
                try:p.wait(timeout=1)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=1)
        for t in readers:
            if t.ident is not None:t.join(timeout=1)
        for p in owned:
            for f in [p.stdout,p.stderr]:
                if f and not f.closed:f.close()
        for c in clients:atexit.unregister(c.close)
        result=dict(source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),name=name,mode=mode,fault=fault,close_fault=close_fault,started_ns=start,pre_external_cleanup=before,after_external_cleanup=dict(process_poll=[p.poll() for p in owned],reader_alive=[t.is_alive() for t in readers]),ended_ns=time.perf_counter_ns(),physical_input=False,model=False)
        (out/'case-result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
        if temp:temp.cleanup()
class StartupOwnershipTests(unittest.TestCase):
    def test_missing_fixture_closes_cooperative_child_and_client(self):
        with fixture('missing-fixture') as s:
            with self.assertRaisesRegex(RuntimeError,'v28 requires a loaded fixture receipt'):s['subject'].main()
            self.assertIsNotNone(s['owned'][0].poll())
            self.assertFalse(s['readers'][0].is_alive())
            self.assertEqual(s['clients'][0].closes,1)
            events=[json.loads(x) for x in s['trace'].read_text().splitlines()]
            self.assertEqual([r['event'] for r in events],['started','eof','closed'])
            self.assertFalse(any(r['event']=='command' for r in events))
    def test_noncooperative_owned_child_is_terminated_after_eof(self):
        with fixture('noncooperative',mode='noncooperative') as s:
            start=time.monotonic()
            with self.assertRaisesRegex(RuntimeError,'loaded fixture'):s['subject'].main()
            self.assertLess(time.monotonic()-start,4)
            self.assertIsNotNone(s['owned'][0].poll())
            self.assertFalse(s['readers'][0].is_alive())
            self.assertEqual(s['clients'][0].closes,1)
            events=[json.loads(x) for x in s['trace'].read_text().splitlines()]
            self.assertEqual([r['event'] for r in events],['started','eof'])
    def test_normal_zero_iteration_finish_is_unchanged(self):
        with fixture('normal',mode='normal') as s:
            s['subject'].main()
            self.assertEqual(s['owned'][0].poll(),0)
            self.assertEqual(s['clients'][0].closes,1)
            events=[json.loads(x) for x in s['trace'].read_text().splitlines()]
            self.assertEqual([r['command'] for r in events if r['event']=='command'],[{'op':'finish'}])
            self.assertTrue((s['out']/'controller'/'report.json').exists())
            self.assertFalse((s['out']/'controller'/'startup-cleanup.json').exists())
    def test_initialize_failure_closes_client_without_session_acquisition(self):
        with fixture('initialize',fault='initialize') as s:
            with self.assertRaisesRegex(ValueError,'injected initialize error'):s['subject'].main()
            self.assertFalse(s['owned']);self.assertEqual(s['clients'][0].closes,1)
    def test_spawn_failure_closes_client_without_session(self):
        with fixture('spawn',fault='spawn') as s:
            with self.assertRaisesRegex(OSError,'injected session spawn error'):s['subject'].main()
            self.assertFalse(s['owned']);self.assertEqual(s['clients'][0].closes,1)
    def test_cleanup_error_preserves_startup_error_and_reports_incomplete(self):
        with fixture('cleanup-error',fault='initialize',close_fault=True) as s:
            with self.assertRaisesRegex(ValueError,'injected initialize error'):s['subject'].main()
            data=json.loads((s['out']/'controller'/'startup-cleanup.json').read_text())
            self.assertFalse(data['client_closed'])
            self.assertTrue(data['errors'])
            self.assertFalse(data['input_release_verified'])
    def test_reader_start_failure_closes_acquired_session(self):
        with fixture('reader-start',fault='reader_start') as s:
            with self.assertRaisesRegex(RuntimeError,'injected stdout reader start error'):s['subject'].main()
            self.assertEqual(s['owned'][0].poll(),0)
            self.assertEqual(s['clients'][0].closes,1)
            data=json.loads((s['out']/'controller'/'startup-cleanup.json').read_text())
            self.assertFalse(data['reader_joined'])
            self.assertTrue(data['errors'])
            self.assertFalse(s['owned'][0].stdout.closed)
    def test_stderr_overflow_retains_prefix_and_reports_partial_evidence(self):
        with fixture('stderr-overflow',mode='stderr-overflow') as s:
            with self.assertRaisesRegex(RuntimeError,'loaded fixture'):s['subject'].main()
            self.assertEqual(s['owned'][0].poll(),0)
            data=json.loads((s['out']/'controller'/'startup-cleanup.json').read_text())
            self.assertEqual((s['out']/'controller'/'startup-stderr.bin').read_bytes(),b'x'*65536)
            self.assertFalse(data['stderr_complete'])
            self.assertEqual(data['stderr_bytes'],65536)
            self.assertEqual(data['errors'],['startup stderr exceeded 65536 bytes; retained prefix'])
            self.assertTrue(data['client_closed'])
            self.assertFalse(data['input_release_verified'])
if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--child':child(*sys.argv[2:])
    else:unittest.main()
