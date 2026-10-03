"""Ordinary repair regression; literal handler and cleanup, no native subjects."""
import ast,hashlib,json,os,pathlib,sys,types,unittest
R=pathlib.Path(__file__).resolve().parent
SOURCE=R/'map01_overlap_controller_v39.py';ROWS=[]
source=SOURCE.read_bytes();module=ast.parse(source)
functions=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in {'_startup_exception_text','_startup_exception_details','_note_startup_exception','_close_failed_startup'}]
main=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='main')
handler=next(n for n in ast.walk(main) if isinstance(n,ast.ExceptHandler) and n.name=='startup_error')
invoke=ast.parse('def invoke(primary):\n try:\n  raise primary\n except BaseException as startup_error:\n  pass\n').body[0]
invoke.body[0].handlers=[handler]
literal=ast.fix_missing_locations(ast.Module(body=functions+[invoke],type_ignores=[]))
class Regression(unittest.TestCase):
 def check_case(self,case):
  trace=[];attempts=[];closed=[];unregistered=[];escaped=None
  class Primary(ValueError):
   def __str__(self):
    if case=='combined_baseexception_hooks':trace.append('str');raise SystemExit('diagnostic str')
    if case=='non_string_str':return 17
    return '起動失敗 — diagnostic regression'
   def add_note(self,note):
    trace.append('note')
    if case=='combined_baseexception_hooks':raise KeyboardInterrupt('diagnostic note')
    return super().add_note(note)
   def __getattribute__(self,name):
    if name=='add_note' and case=='note_lookup_fault':trace.append('note_lookup');raise SystemExit('diagnostic lookup')
    return super().__getattribute__(name)
  class FaultMeta(type):
   def __getattribute__(self,name):
    if name=='__name__':trace.append('type_name');raise KeyboardInterrupt('diagnostic name')
    return super().__getattribute__(name)
  class NameFault(ValueError,metaclass=FaultMeta):pass
  class CleanupError(OSError):
   def __repr__(self):trace.append('repr');raise GeneratorExit('diagnostic repr')
  class RecordError(OSError):
   def __repr__(self):trace.append('record_repr');raise SystemExit('record repr')
  primary=NameFault('type name fault') if case=='type_name_fault' else Primary('initial')
  class Client:
   def close(self,timeout):
    trace.append('close');self.timeout=timeout
    if case=='combined_baseexception_hooks':raise CleanupError('cleanup')
    if case in {'note_lookup_fault','ordinary_cleanup_error'}:raise OSError('ordinary close failure')
    closed.append(True)
  class Record:
   def write_text(self,text):
    trace.append('record');attempts.append(json.loads(text))
    if case=='note_lookup_fault':raise RecordError('record')
    if case=='record_non_oserror':raise RuntimeError('record failure')
    if case=='record_keyboardinterrupt':raise KeyboardInterrupt('record interrupt')
  class Out:
   def __truediv__(self,name):assert name=='startup-cleanup.json';return Record()
  class BrokenEvents:
   def __iter__(self):trace.append('events_iter');raise RuntimeError('event copy failure')
  events=BrokenEvents() if case=='event_copy_fault' else [object()] if case=='json_serialization_fault' else []
  def unregister(callback):trace.append('unregister');unregistered.append(True)
  scope={'process':None,'reader_thread':None,'planner_client':Client(),'args':types.SimpleNamespace(out=Out()),'all_events':events,'json':json,'atexit':types.SimpleNamespace(unregister=unregister)}
  exec(compile(literal,'literal-controller-startup','exec'),scope)
  try:scope['invoke'](primary)
  except BaseException as error:escaped=error
  same=escaped is primary
  notes=BaseException.__getattribute__(primary,'__dict__').get('__notes__',[])
  row={'case':case,'same_primary':same,'trace':trace,'record_attempts':attempts,'notes':notes,'client_closed':bool(closed),'callback_removed':bool(unregistered)};ROWS.append(row)
  self.assertTrue(same,'diagnostics replaced original startup exception')
  bad_record=case in {'event_copy_fault','json_serialization_fault'}
  self.assertEqual(len(attempts),0 if bad_record else 1)
  close_failed=case in {'combined_baseexception_hooks','note_lookup_fault','ordinary_cleanup_error'}
  self.assertEqual(bool(closed),not close_failed);self.assertEqual(bool(unregistered),not close_failed)
  if attempts:
   d=attempts[0];self.assertIs(d['client_closed'],not close_failed);self.assertIs(d['input_release_verified'],False)
   self.assertEqual(d['startup_events'],[])
   if case in {'combined_baseexception_hooks','non_string_str'}:self.assertEqual(d['startup_error']['message'],'<exception text unavailable>')
   if case=='type_name_fault':self.assertEqual(d['startup_error']['type'],'<exception type unavailable>')
   if case=='combined_baseexception_hooks':self.assertEqual(d['errors'],['planner close: <exception text unavailable>'])
  if case=='combined_baseexception_hooks':self.assertEqual(trace,['close','repr','str','record','note']);self.assertEqual(notes,[])
  if case=='note_lookup_fault':self.assertEqual(trace,['close','record','record_repr','note_lookup','note_lookup']);self.assertEqual(notes,[])
  if case=='ordinary_cleanup_error':self.assertEqual(notes,['startup cleanup incomplete; see startup-cleanup.json'])
  if case in {'record_non_oserror','record_keyboardinterrupt','event_copy_fault','json_serialization_fault'}:self.assertEqual(len(notes),1);self.assertTrue(notes[0].startswith('startup cleanup record failed: '))
  if case=='unicode_control':self.assertEqual(attempts[0]['startup_error']['message'],'起動失敗 — diagnostic regression');self.assertEqual(notes,[])
for case in ('combined_baseexception_hooks','note_lookup_fault','type_name_fault','non_string_str','record_non_oserror','record_keyboardinterrupt','event_copy_fault','json_serialization_fault','ordinary_cleanup_error','unicode_control'):
 setattr(Regression,'test_'+case,lambda self,c=case:self.check_case(c))
if __name__=='__main__':
 unittest.main()
