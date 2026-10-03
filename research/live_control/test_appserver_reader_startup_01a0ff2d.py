import base64,datetime,hashlib,io,json,os,subprocess,sys,tempfile,threading,types,unittest
from pathlib import Path
from unittest.mock import patch
import codex_app_server_client_v2 as mod
OUT=None if not os.environ.get('I09_OUT') else Path(os.environ['I09_OUT'])

class FakeProcess:
    def __init__(self,stop_error=False,close_error=False):
        self.stdin=io.StringIO();self.stdout=io.StringIO();self.stderr=io.BytesIO()
        self.returncode=None;self.calls=[];self.stop_error=stop_error
        if close_error:
            self.stdin.close=lambda: (_ for _ in ()).throw(OSError('stdin close refused'))
    def poll(self):return self.returncode
    def terminate(self):
        self.calls.append('terminate')
        if self.stop_error:raise OSError('terminate refused')
        self.returncode=1
    def kill(self):self.calls.append('kill');self.returncode=1
    def wait(self,timeout=None):self.calls.append('wait');return self.returncode

class Subject(mod.CodexAppServerClient):
    def _read(self):
        self.trace.append('read_stdout')
        if self.block_reader:
            self.entered.set();self.release.wait(5)
        else:super()._read()
    def _read_stderr(self):self.trace.append('read_stderr');super()._read_stderr()

class Startup(unittest.TestCase):
    def exercise(self,kind):
        primary=KeyboardInterrupt('directed reader startup interruption')
        obj=object.__new__(Subject);obj.trace=[];obj.block_reader=kind=='running';obj.entered=threading.Event();obj.release=threading.Event()
        pending_entered=threading.Event();pending_release=threading.Event()
        created=[];calls=[];caught=None;peer=None;row={'case':kind,'pid':os.getpid(),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        class Pending(threading.Thread):
            def _bootstrap_inner(self):
                pending_entered.set();pending_release.wait(5);super()._bootstrap_inner()
            def start(self):
                original_wait=self._started.wait
                def interrupted_wait(timeout=None):
                    if not pending_entered.wait(2):raise AssertionError('pending bootstrap missing')
                    raise primary
                self._started.wait=interrupted_wait
                try:super().start()
                finally:self._started.wait=original_wait
        def factory_thread(*args,**kwargs):
            index=len(created)
            if kind=='construct_second' and index==1:raise primary
            t=Pending(*args,**kwargs) if kind=='pending_second' and index==1 else threading.Thread(*args,**kwargs)
            created.append(t)
            if (kind=='first' and index==0) or (kind in ('second','running','cleanup_faults','real_second') and index==1):
                def refuse():
                    if kind=='running' and not obj.entered.wait(2):raise AssertionError('running reader missing')
                    if kind not in ('running','real_second') and index==1:created[0].join(2)
                    raise primary
                t.start=refuse
            return t
        api=types.SimpleNamespace(Lock=threading.Lock,Condition=threading.Condition,Thread=factory_thread)
        with tempfile.TemporaryDirectory(prefix='i09-owned-') as temp:
            journal=Path(temp)/'journal.jsonl'
            def factory(command,**kwargs):
                nonlocal peer
                calls.append('factory')
                if kind=='real_second':
                    peer=subprocess.Popen([sys.executable,'-u','-c','import sys; sys.stdout.write("{\\"method\\":\\"ready\\"}\\n"); sys.stdout.flush(); sys.stdin.read()'],**kwargs)
                else:peer=FakeProcess(stop_error=kind=='cleanup_faults',close_error=kind=='cleanup_faults')
                return peer
            try:
                with patch.object(mod,'threading',api):
                    try:Subject.__init__(obj,['INERT_ONLY'],process_factory=factory,journal_path=journal)
                    except BaseException as e:caught=e
                row.update(primary_preserved=caught is primary,primary_type=type(caught).__name__,factory_calls=len(calls),journal_closed=obj._journal.closed,stream_closed={k:getattr(peer,k).closed for k in ('stdin','stdout','stderr')},peer_returncode=peer.poll(),notes=list(getattr(caught,'__notes__',[])),trace_before_release=list(obj.trace),created_threads=len(created))
                pending_release.set();obj.release.set()
                for t in created:
                    if t.ident is not None:t.join(2)
                    elif kind=='pending_second' and t is created[-1]:
                        t._started.wait(2);t.join(2)
                row['trace_after_release']=list(obj.trace)
                row['threads_after_release']=[t.is_alive() for t in created]
                self.assertIs(caught,primary)
                self.assertEqual(len(calls),1)
                if kind=='running':
                    self.assertFalse(row['journal_closed'])
                    self.assertTrue(all(not v for v in row['stream_closed'].values()))
                    self.assertTrue(any('TimeoutError' in n for n in row['notes']))
                elif kind=='cleanup_faults':
                    self.assertTrue(row['journal_closed']);self.assertFalse(row['stream_closed']['stdin'])
                    self.assertTrue(row['stream_closed']['stdout']);self.assertTrue(row['stream_closed']['stderr'])
                    self.assertGreaterEqual(len(row['notes']),2)
                else:
                    self.assertTrue(row['journal_closed'],'journal left open')
                    self.assertTrue(all(row['stream_closed'].values()),'pipe left open')
                    self.assertIsNotNone(row['peer_returncode'],'owned child not retired')
                if kind=='pending_second':self.assertNotIn('read_stderr',row['trace_after_release'])
                self.assertFalse(any(row['threads_after_release']))
            except BaseException as e:row.update(outcome='FAIL',test_error_type=type(e).__name__,test_error=str(e));raise
            else:row['outcome']='PASS'
            finally:
                pending_release.set();obj.release.set()
                for t in created:
                    if t.ident is not None:t.join(2)
                if peer is not None:
                    if peer.poll() is None:
                        peer.kill();peer.wait(timeout=2)
                    for name in ('stdin','stdout','stderr'):
                        stream=getattr(peer,name)
                        if not stream.closed:
                            try:stream.close()
                            except OSError:
                                # Only the deliberately overridden fake stdin is left open.
                                io.StringIO.close(stream)
                if getattr(obj,'_journal',None) is not None:obj._journal.close()
                row['driver_cleanup_complete']=peer is None or (peer.poll() is not None and all(getattr(peer,k).closed for k in ('stdin','stdout','stderr')) and obj._journal.closed)
                row['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
                if OUT is not None:
                    (OUT/(kind+'.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8')
    def test_first_start_refusal(self):self.exercise('first')
    def test_second_start_refusal(self):self.exercise('second')
    def test_second_thread_construction_refusal(self):self.exercise('construct_second')
    def test_pending_second_cancels_future_access(self):self.exercise('pending_second')
    def test_running_reader_retains_resources(self):self.exercise('running')
    def test_independent_cleanup_faults(self):self.exercise('cleanup_faults')
    def test_real_second_failure_retires_child_and_pipes(self):self.exercise('real_second')
    def test_real_healthy_protocol_and_stderr(self):
        with tempfile.TemporaryDirectory(prefix='i09-control-') as temp:
            p=Path(temp)/'healthy.jsonl';peer=None
            def factory(command,**kwargs):
                nonlocal peer
                peer=subprocess.Popen([sys.executable,'-u','-c','import sys,json; sys.stderr.buffer.write(b"diag\\xff"); sys.stderr.flush(); r=json.loads(sys.stdin.readline()); print(json.dumps({"id":r["id"],"result":"unknown"}),flush=True); sys.stdin.read()'],**kwargs)
                return peer
            client=mod.CodexAppServerClient(['INERT_ONLY'],process_factory=factory,journal_path=p)
            try:self.assertEqual(client.request('inert',timeout=2),'unknown')
            finally:
                client.close(timeout=2)
                for s in (peer.stdin,peer.stdout,peer.stderr):s.close()
            snap=client.stderr_snapshot();self.assertEqual(snap['tail'],b'diag\xff');self.assertTrue(snap['complete'])
            self.assertFalse(client._reader.is_alive());self.assertFalse(client._stderr_reader.is_alive())
            if OUT is not None:
                (OUT/'healthy.json').write_text(json.dumps({'case':'healthy','outcome':'PASS','peer_pid':peer.pid,'peer_returncode':peer.returncode,'result':'unknown','stderr_b64':base64.b64encode(snap['tail']).decode(),'complete':snap['complete'],'journal_closed':client._journal.closed,'pipes_closed':all(s.closed for s in (peer.stdin,peer.stdout,peer.stderr)),'journal_b64':base64.b64encode(p.read_bytes()).decode()},indent=2)+'\n')

if __name__=='__main__':unittest.main(verbosity=2)
