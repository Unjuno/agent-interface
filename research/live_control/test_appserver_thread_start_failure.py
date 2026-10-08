import builtins,datetime,json,os,subprocess,sys,tempfile,threading,types,unittest
from pathlib import Path
from unittest.mock import patch
import codex_app_server_client_v2 as source

class CleanupFault(OSError):pass
class HostileError(OSError):
    def add_note(self,text):raise AssertionError('hostile override')
class RefusedThread:
    ident=None
    error=None
    def __init__(self,**kwargs):self.kwargs=kwargs
    def start(self):raise self.error
class Stream:
    def __init__(self,real,mode='healthy'):self.real=real;self.fd=real.fileno();self.attempts=0;self.mode=mode
    def close(self):
        self.attempts+=1
        if self.mode=='before':raise CleanupFault('before close')
        self.real.close()
        if self.mode=='after':raise CleanupFault('after close')
    def __getattr__(self,n):return getattr(self.real,n)
class Process:
    def __init__(self,streams,fault):self.stdin,self.stdout,self.stderr=streams;self.returncode=None;self.events=[];self.fault=fault
    def poll(self):self.events.append('poll');return self.returncode
    def terminate(self):
        self.events.append('terminate')
        if self.fault=='terminate':raise CleanupFault('terminate')
    def wait(self,timeout):
        self.events.append('wait')
        if self.fault=='wait' or (self.fault=='timeout' and self.events.count('wait')==1):raise source.subprocess.TimeoutExpired('owned-double',timeout)
        self.returncode=1;return 1
    def kill(self):self.events.append('kill')

class ThreadStartupRegression(unittest.TestCase):
    def exercise(self,error=None,fault=None,stream_fault=None,journal_fault=None,journal=True):
        if error is None:error=OSError('thread refused')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);all_handles=[];opened=[]
            def native(name,mode='healthy'):
                x=Stream(builtins.open(root/name,'w+',encoding='utf-8'),mode);all_handles.append(x);return x
            process=Process([native(n,stream_fault if n=='out' and stream_fault else 'healthy') for n in ['in','out','err']],fault)
            def open_journal(*args,**kwargs):
                x=Stream(builtins.open(*args,**kwargs),journal_fault or 'healthy');all_handles.append(x);opened.append(x);return x
            RefusedThread.error=error
            local=types.SimpleNamespace(Lock=threading.Lock,Condition=threading.Condition,Thread=RefusedThread)
            try:
                with patch.object(source,'threading',local),patch.object(source,'open',open_journal,create=True):
                    try:source.CodexAppServerClient(['inert'],process_factory=lambda *a,**k:process,journal_path=root/'journal' if journal else None)
                    except BaseException as caught:self.assertIs(caught,error)
                    else:self.fail('thread refusal returned')
                self.assertEqual(process.events[:2],['poll','terminate'])
                self.assertEqual('kill' in process.events,fault in ['timeout','wait'])
                for x in all_handles:
                    self.assertEqual(x.attempts,1)
                    expected=x.mode!='before';self.assertIs(x.real.closed,expected)
                    if expected:
                        with self.assertRaises(OSError):os.fstat(x.fd)
                    else:os.fstat(x.fd)
                if fault is None:self.assertEqual(process.returncode,1)
                if fault in ['terminate','wait'] or stream_fault or journal_fault:
                    if getattr(error,'__notes__',None)!=42:self.assertTrue(error.__notes__)
                return process.events
            finally:
                for x in all_handles:x.real.close()
    def test_oserror_retires_process_pipes_and_journal(self):self.exercise()
    def test_keyboardinterrupt_preserves_primary_and_releases(self):self.exercise(KeyboardInterrupt('fixture'))
    def test_without_journal_still_retires_process_and_pipes(self):self.exercise(journal=False)
    def test_terminate_error_preserves_primary_and_attempts_all_files(self):self.exercise(fault='terminate')
    def test_wait_timeout_kills_then_reaps(self):self.exercise(fault='timeout')
    def test_second_wait_timeout_preserves_primary_and_attempts_all_files(self):self.exercise(fault='wait')
    def test_pipe_before_close_fault_preserves_primary_and_closes_other_files(self):self.exercise(stream_fault='before')
    def test_pipe_after_close_fault_preserves_primary(self):self.exercise(stream_fault='after')
    def test_journal_before_close_fault_preserves_primary(self):self.exercise(journal_fault='before')
    def test_journal_after_close_fault_preserves_primary(self):self.exercise(journal_fault='after')
    def test_hostile_add_note_override_is_bypassed(self):self.exercise(HostileError('primary'),fault='terminate')
    def test_malformed_notes_do_not_replace_primary(self):
        error=OSError('primary');error.__notes__=42;self.exercise(error,fault='terminate')
    def test_real_owned_process_and_native_pipe_journal_fds_are_closed_by_source(self):
        with tempfile.TemporaryDirectory() as directory:
            acquired=[];journals=[];descriptors={};error=OSError('native thread refusal')
            def factory(*args,**kwargs):
                proc=subprocess.Popen(*args,**kwargs);acquired.append(proc)
                descriptors.update({n:getattr(proc,n).fileno() for n in ['stdin','stdout','stderr']});return proc
            def open_journal(*args,**kwargs):
                f=builtins.open(*args,**kwargs);journals.append(f);descriptors['journal']=f.fileno();return f
            RefusedThread.error=error;local=types.SimpleNamespace(Lock=threading.Lock,Condition=threading.Condition,Thread=RefusedThread)
            try:
                with patch.object(source,'threading',local),patch.object(source,'open',open_journal,create=True):
                    try:source.CodexAppServerClient([sys.executable,'-c','import time;time.sleep(6)'],process_factory=factory,journal_path=Path(directory)/'journal')
                    except BaseException as caught:self.assertIs(caught,error)
                    else:self.fail('native thread refusal returned')
                self.assertEqual(len(acquired),1);proc=acquired[0];self.assertIsInstance(proc.poll(),int)
                observations={}
                for n,fd in descriptors.items():
                    with self.assertRaises(OSError):os.fstat(fd)
                    stream=journals[0] if n=='journal' else getattr(proc,n);self.assertTrue(stream.closed)
                    observations[n]={'fd_open':False,'textio_closed':stream.closed}
                metric={'child_pid':proc.pid,'child_exit':proc.returncode,'same_primary':True,'source_closed_resources':observations,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'driver_cleanup_after_assertions':True}
                phase=os.environ.get('THREAD_REPAIR_PHASE')
                if phase:
                    (Path(__file__).parent/(phase+'-native.json')).write_bytes(json.dumps(metric,sort_keys=True,indent=2).encode()+b'\n')
            finally:
                for proc in acquired:
                    if proc.poll() is None:proc.kill();proc.wait(timeout=2)
                    for n in ['stdin','stdout','stderr']:getattr(proc,n).close()
                for f in journals:f.close()
if __name__=='__main__':unittest.main()
