"""Injected prelaunch failure + real journal handle regressions; no OS peer."""
import datetime,hashlib,json,os,tempfile,threading,unittest
from pathlib import Path
import codex_app_server_client_v2 as client_module
Client=client_module.CodexAppServerClient
image=Path(client_module.__file__).read_bytes()
location=os.environ.get('APPSERVER_STARTUP_EVIDENCE_DIR')
out=None if not location else Path(location)
class FailingClose:
 def __init__(self,real):self.real=real;self.error=OSError('owned journal close failure');self.calls=0
 @property
 def closed(self):return self.real.closed
 def close(self):self.calls+=1;raise self.error
class Startup(unittest.TestCase):
 def exercise(self,error,journal=True,close_error=False):
  row={'case':self._testMethodName,'source_sha256':hashlib.sha256(image).hexdigest(),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'factory_calls':0,'actual_os_children':0,'close_failure_injected':close_error}
  instance=object.__new__(Client);caught=None;wrapped=[]
  original_open=open
  def owned_open(*args,**kwargs):
   value=FailingClose(original_open(*args,**kwargs));wrapped.append(value);return value
  def fail(command,**kwargs):
   row['factory_calls']+=1;row['factory_kwargs']={k:v for k,v in kwargs.items() if k not in ('cwd','stdin','stdout','stderr')};raise error
  with tempfile.TemporaryDirectory(prefix='i06-owned-') as temp:
   path=Path(temp)/'startup.jsonl';before={t.ident for t in threading.enumerate()}
   if close_error:client_module.__dict__['open']=owned_open
   try:
    try:Client.__init__(instance,['DO_NOT_LAUNCH'],process_factory=fail,journal_path=path if journal else None)
    except BaseException as e:caught=e
    row.update(original_error_preserved=caught is error,error_type=type(caught).__name__,original_traceback_has_factory=any(f.tb_frame.f_code.co_name=='fail' for f in traceback_frames(caught)),journal_closed=None if not journal else instance._journal.closed,journal_bytes_b64='' if not journal else __import__('base64').b64encode(path.read_bytes()).decode(),threads_unchanged=before=={t.ident for t in threading.enumerate()},cleanup_error_chained=bool(wrapped and caught.__cause__ is wrapped[0].error),journal_close_calls=None if not wrapped else wrapped[0].calls,process_attribute_created=hasattr(instance,'process'))
    self.assertIs(caught,error)
    self.assertEqual(row['factory_calls'],1)
    self.assertTrue(row['threads_unchanged'])
    self.assertFalse(row['process_attribute_created'])
    if close_error:
     self.assertIs(caught.__cause__,wrapped[0].error)
     self.assertFalse(row['journal_closed'])
    elif journal:self.assertTrue(row['journal_closed'],'startup failed but exclusive journal remains open')
   except BaseException as e:row['test_outcome']='FAIL';row['test_error_type']=type(e).__name__;row['test_error_message']=str(e);raise
   else:row['test_outcome']='PASS'
   finally:
    client_module.__dict__.pop('open',None)
    if journal:
     handle=wrapped[0].real if wrapped else getattr(instance,'_journal',None)
     if handle is not None:handle.close()
     row['driver_final_journal_closed']=handle is None or handle.closed
    row['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    if out is not None:
     (out/(self._testMethodName+'.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf-8')
 def test_missing_executable_retires_journal(self):self.exercise(FileNotFoundError('owned missing executable'))
 def test_oserror_retires_journal(self):self.exercise(OSError('owned launch refusal'))
 def test_interrupt_retires_journal(self):self.exercise(KeyboardInterrupt('owned startup interruption'))
 def test_no_journal_preserves_original_error(self):self.exercise(OSError('owned without journal'),journal=False)
 def test_failed_close_keeps_startup_error_and_exposes_cleanup(self):self.exercise(OSError('owned startup primary'),close_error=True)
def traceback_frames(e):
 frame=e.__traceback__
 while frame:
  yield frame;frame=frame.tb_next
if __name__=='__main__':unittest.main(verbosity=2)
