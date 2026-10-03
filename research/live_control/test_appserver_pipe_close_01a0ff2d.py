import base64,datetime,io,json,os,subprocess,sys,tempfile,threading,unittest
from pathlib import Path
import codex_app_server_client_v2 as mod
OUT=None if not os.environ.get('I10_OUT') else Path(os.environ['I10_OUT'])
class RefusingStream(io.StringIO):
    def __init__(self,error):super().__init__();self.error=error;self.calls=0
    def close(self):self.calls+=1;raise self.error
class Reader:
    def __init__(self,live=False):self.live=live;self.joins=0
    def join(self,timeout=None):self.joins+=1
    def is_alive(self):return self.live
class DeadProcess:
    def __init__(self):self.stdin=io.StringIO();self.stdout=io.StringIO();self.stderr=io.StringIO()
    def poll(self):return 0
class Close(unittest.TestCase):
    def exercise(self,kind):
        c=object.__new__(mod.CodexAppServerClient);c.process=DeadProcess();c._reader=Reader(kind=='live_stdout');c._stderr_reader=Reader(kind=='live_stderr');c._journal_lock=threading.Lock()
        primary=OSError('directed first close refusal');secondary=KeyboardInterrupt('directed later close refusal');caught=None
        with tempfile.TemporaryDirectory(prefix='i10-owned-') as temp:
            c._journal=open(Path(temp)/'journal.jsonl','x',encoding='utf-8')
            if kind in ('journal_fault','two_faults'):
                c._journal.close()
                c._journal=RefusingStream(primary)
            if kind=='two_faults':c.process.stdin=RefusingStream(secondary)
            if kind=='pipe_fault':c.process.stdin=RefusingStream(primary)
            if kind=='locked_journal':c._journal_lock.acquire()
            row={'case':kind,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid()}
            try:
                try:c.close(timeout=.01)
                except BaseException as e:caught=e
                row.update(error_type=None if caught is None else type(caught).__name__,primary_preserved=caught is primary,notes=list(getattr(caught,'__notes__',[])),journal_closed=c._journal.closed,streams={k:getattr(c.process,k).closed for k in ('stdin','stdout','stderr')},reader_joins=[c._reader.joins,c._stderr_reader.joins],refusal_calls=getattr(c.process.stdin,'calls',0))
                if kind in ('live_stdout','live_stderr'):
                    self.assertIsInstance(caught,TimeoutError);self.assertFalse(row['journal_closed']);self.assertTrue(all(v is False for v in row['streams'].values()))
                else:
                    if kind=='locked_journal':self.assertIsInstance(caught,TimeoutError);self.assertFalse(row['journal_closed'])
                    elif kind in ('journal_fault','pipe_fault','two_faults'):self.assertIs(caught,primary)
                    else:self.assertIsNone(caught)
                    if kind in ('journal_fault','two_faults'):self.assertFalse(row['journal_closed'])
                    elif kind!='locked_journal':self.assertTrue(row['journal_closed'])
                    if kind in ('pipe_fault','two_faults'):
                        self.assertFalse(row['streams']['stdin']);self.assertTrue(row['streams']['stdout']);self.assertTrue(row['streams']['stderr'])
                    else:self.assertTrue(all(row['streams'].values()),'owned pipes left open after both readers retired')
                    if kind=='two_faults':self.assertTrue(any('KeyboardInterrupt' in n for n in row['notes']))
                    if kind=='repeat':c.close(timeout=.01);row['second_close_completed']=True
            except BaseException as e:row.update(outcome='FAIL',assertion_type=type(e).__name__,assertion_message=str(e));raise
            else:row['outcome']='PASS'
            finally:
                if kind=='locked_journal':c._journal_lock.release()
                for s in (c._journal,c.process.stdin,c.process.stdout,c.process.stderr):
                    if not s.closed:
                        if isinstance(s,RefusingStream):io.StringIO.close(s)
                        else:s.close()
                row['driver_final_all_closed']=all(s.closed for s in (c._journal,c.process.stdin,c.process.stdout,c.process.stderr));row['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
                if OUT is not None:
                    (OUT/(kind+'.json')).write_text(json.dumps(row,indent=2)+'\n')
    def test_normal_close(self):self.exercise('normal')
    def test_repeat_close(self):self.exercise('repeat')
    def test_journal_failure_pipes_still_closed(self):self.exercise('journal_fault')
    def test_journal_lock_timeout_pipes_still_closed(self):self.exercise('locked_journal')
    def test_pipe_failure_does_not_skip_later_pipes(self):self.exercise('pipe_fault')
    def test_first_error_retained_and_later_error_exposed(self):self.exercise('two_faults')
    def test_live_stdout_resources_retained(self):self.exercise('live_stdout')
    def test_live_stderr_resources_retained(self):self.exercise('live_stderr')
    def test_real_direct_child_and_all_streams_closed(self):
        peer=None;row={'case':'real','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};caught=None
        with tempfile.TemporaryDirectory(prefix='i10-real-') as temp:
            def factory(command,**kwargs):
                nonlocal peer
                peer=subprocess.Popen([sys.executable,'-u','-c','import sys,json; r=json.loads(sys.stdin.readline()); sys.stderr.buffer.write(b"diag\\xff"); sys.stderr.flush(); print(json.dumps({"id":r["id"],"result":"owned"}),flush=True); sys.stdin.read()'],**kwargs)
                return peer
            c=mod.CodexAppServerClient(['INERT_ONLY'],process_factory=factory,journal_path=Path(temp)/'journal.jsonl')
            try:
                result=c.request('inert',timeout=2);c.close(timeout=2)
                row.update(result=result,peer_pid=peer.pid,peer_returncode=peer.returncode,readers_alive=[c._reader.is_alive(),c._stderr_reader.is_alive()],streams={k:getattr(peer,k).closed for k in ('stdin','stdout','stderr')},journal_closed=c._journal.closed,stderr_b64=base64.b64encode(c.stderr_snapshot()['tail']).decode())
                self.assertEqual(result,'owned');self.assertIsNotNone(peer.returncode);self.assertFalse(any(row['readers_alive']));self.assertTrue(row['journal_closed']);self.assertTrue(all(row['streams'].values()),'real Popen pipes remain open');self.assertEqual(base64.b64decode(row['stderr_b64']),b'diag\xff')
            except BaseException as e:row.update(outcome='FAIL',error_type=type(e).__name__,error=str(e));raise
            else:row['outcome']='PASS'
            finally:
                if peer.poll() is None:peer.kill();peer.wait(timeout=2)
                for s in (peer.stdin,peer.stdout,peer.stderr):
                    if not s.closed:s.close()
                row['driver_final_all_closed']=all(s.closed for s in (peer.stdin,peer.stdout,peer.stderr));row['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
                if OUT is not None:
                    (OUT/'real.json').write_text(json.dumps(row,indent=2)+'\n')
if __name__=='__main__':unittest.main(verbosity=2)
