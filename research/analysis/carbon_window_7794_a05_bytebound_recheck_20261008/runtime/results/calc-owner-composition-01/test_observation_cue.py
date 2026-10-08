import copy, hashlib, io, json, subprocess, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from PIL import Image
from observation_cue import CalcObservationCue

TSV=b'level\tleft\ttop\twidth\theight\tconf\ttext\n5\t92\t185\t20\t10\t95\t731\n5\t92\t205\t20\t10\t95\t864\n'
class CueTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);self.captures=self.root/'captures';self.captures.mkdir()
  self.image=Image.new('RGB',(1280,800),'white');buf=io.BytesIO();self.image.save(buf,format='PNG');self.data=buf.getvalue()
  self.path=self.captures/'frame.png';self.path.write_bytes(self.data);self.now=10_000_000_000
  self.binding={'surface':20,'focus':21,'geometry':[0,0,1280,800]}
  self.state={'scope':'calc-scope','revision':1,'binding':self.binding,'focus_ok':True,'review_required':False,'sequence':3,'title':'book.xlsx - LibreOffice Calc','busy':False,'recovery_required':False}
  self.approved={k:copy.deepcopy(self.state[k]) for k in ('scope','revision','binding')}
  self.approved.update(geometry_reviewed=True,image_size=[1280,800],titles=[self.state['title']])
  self.native={'sequence':3,'capture_ns':self.now-100_000_000,'binding_revision':1,'pointer_binding':copy.deepcopy(self.binding),
   'native':{'sha256':'raw-capture-identity','frame':'screen_physical_px','region':[0,0,1280,800],'width':1280,'height':800,'native_window_id':20,'capture_ended_ns':self.now-90_000_000,
    'artifact':{'path':str(self.path),'sha256':hashlib.sha256(self.data).hexdigest(),'bytes':len(self.data),'mime_type':'image/png','source_raw_sha256':'raw-capture-identity','width':1280,'height':800}}}
  self.calls=[]
 def run_ocr(self,command,**kw):
  self.calls.append((command,kw));return SimpleNamespace(returncode=0,stdout=TSV,stderr=b'')
 def adapter(self,runner=None):
  return CalcObservationCue(capture_root=self.captures,evidence_root=self.root/'evidence',approved=self.approved,context=lambda:copy.deepcopy(self.state),deadline_ns=self.now+2_000_000_000,clock=lambda:self.now,runner=runner or self.run_ocr)
 def result(self,runner=None):return self.adapter(runner)(self.native,self.image)
 def test_exact_original_png_and_fixed_command(self):
  self.assertEqual(self.result(),{'cells':'filled','sheet_context':True,'source_context_verified':True})
  command,kw=self.calls[0];self.assertEqual(command,['tesseract','stdin','stdout','--psm','11','tsv']);self.assertEqual(kw['input'],self.data);self.assertLessEqual(kw['timeout'],1)
  record=json.loads((self.root/'evidence/001.json').read_text());self.assertFalse(record['input_dispatched']);self.assertFalse(record['extra_capture'])
 def test_png_hash_mismatch_prevents_ocr(self):
  self.path.write_bytes(self.data+b'changed');self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_changed_rgb_handoff_prevents_ocr(self):
  self.image.putpixel((1,1),(1,2,3));self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_outside_capture_root_prevents_ocr(self):
  outside=self.root/'outside.png';outside.write_bytes(self.data);self.native['native']['artifact']['path']=str(outside)
  self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_source_raw_hash_mismatch(self):
  self.native['native']['artifact']['source_raw_sha256']='different';self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_target_mismatch(self):
  self.native['native']['native_window_id']=22;self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_coordinate_change(self):
  self.native['native']['region']=[20,20,1280,800];self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_stale_capture(self):
  self.native['capture_ns']=self.now-1_500_000_001;self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_future_capture(self):
  self.native['capture_ns']=self.now+1;self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_modal_title(self):
  self.state['title']='Use Excel 2007-365 Format?';self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_focus_changed_before_ocr(self):
  self.state['focus_ok']=False;self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_review_required(self):
  self.state['review_required']=True;self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_observation_replaced(self):
  self.state['sequence']=4;self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_binding_revision_changed(self):
  self.state['revision']=2;self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_focus_changed_during_ocr_discards_valid_digits(self):
  def runner(*a,**kw):self.state['binding']['focus']=22;return self.run_ocr(*a,**kw)
  self.assertEqual(self.result(runner)['cells'],'unknown');self.assertEqual(len(self.calls),1)
 def test_deadline_during_ocr_discards_valid_digits(self):
  def runner(*a,**kw):self.now+=2_000_000_000;return self.run_ocr(*a,**kw)
  self.assertEqual(self.result(runner)['cells'],'unknown')
 def test_ocr_timeout_retains_partial_output_no_retry(self):
  def runner(*a,**kw):self.calls.append((a,kw));raise subprocess.TimeoutExpired(a[0],kw['timeout'],output=b'partial',stderr=b'timeout')
  self.assertEqual(self.result(runner)['cells'],'unknown');self.assertEqual(len(self.calls),1);self.assertEqual((self.root/'evidence/001.tsv').read_bytes(),b'partial')
 def test_ocr_nonzero(self):
  self.assertEqual(self.result(lambda *a,**k:SimpleNamespace(returncode=1,stdout=TSV,stderr=b'error'))['cells'],'unknown')
 def test_wrong_cell_values_remain_wrong(self):
  self.assertEqual(self.result(lambda *a,**k:SimpleNamespace(returncode=0,stdout=TSV.replace(b'864',b'863'),stderr=b''))['cells'],'wrong')
 def test_missing_digits_are_not_blank(self):
  self.assertEqual(self.result(lambda *a,**k:SimpleNamespace(returncode=0,stdout=b'',stderr=b''))['cells'],'unknown')
 def test_reused_sequence_no_second_ocr(self):
  cue=self.adapter();self.assertEqual(cue(self.native,self.image)['cells'],'filled');self.assertEqual(cue(self.native,self.image)['cells'],'unknown');self.assertEqual(len(self.calls),1)
 def test_boolean_revision_is_not_integer_authority(self):
  self.native['binding_revision']=True;self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_busy_session(self):
  self.state['busy']=True;self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_recovery_required(self):
  self.state['recovery_required']=True;self.assertEqual(self.result()['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_context_sampling_failure(self):
  cue=self.adapter();cue.context=lambda:(_ for _ in ()).throw(RuntimeError('window unavailable'))
  self.assertEqual(cue(self.native,self.image)['cells'],'unknown');self.assertEqual(self.calls,[])
 def test_existing_bridge_context_has_no_capture_or_input(self):
  from observation_cue import bridge_context
  b=SimpleNamespace(scope='scope',binding_revision=1,sequence=3,active=None,review_required=False,session=SimpleNamespace(recovery_required=False),_binding=lambda:copy.deepcopy(self.binding),_focus_within_target=lambda:True,_window_title=lambda:'sheet')
  state=bridge_context(b);self.assertEqual(state['binding'],self.binding);self.assertEqual(state['sequence'],3);self.assertFalse(state['busy'])
 def test_primary_review_required(self):
  self.approved['geometry_reviewed']=False
  with self.assertRaises(ValueError):self.adapter()

class GraphConnectionTests(unittest.TestCase):
 setUp=CueTests.setUp
 adapter=CueTests.adapter
 run_ocr=CueTests.run_ocr
 def graph(self,tsv):
  from runtime.core_v1.test_compiled_gui import Driver,interface
  cue=self.adapter(lambda *a,**k:SimpleNamespace(returncode=0,stdout=tsv,stderr=b''))
  driver=Driver();base=driver.observe
  def observe(request):
   record=base(request)
   if record['sequence']==2:
    values=cue(self.native,self.image)
    record['predicates']={'phase':1} if values['cells']=='filled' else {}
   return record
  driver.observe=observe
  def verify(request):
   driver.record('verify_effect',request)
   return {'status':'succeeded' if request['action']=='enter' else 'unavailable','evidence_ref':request['observation']['evidence_ref']}
  driver.verify=verify
  return driver,driver.run(interface())
 def test_exact_cells_allow_save_but_not_persistence_success(self):
  driver,result=self.graph(TSV);self.assertEqual(len(driver.calls['execute']),2);self.assertEqual(result['outcome'],'SAFE_YIELD');self.assertEqual(result['reason'],'effect_unavailable')
 def test_wrong_cells_stop_before_save_preserving_enter_prefix(self):
  driver,result=self.graph(TSV.replace(b'864',b'863'));self.assertEqual(len(driver.calls['execute']),1);self.assertEqual(result['completed_transitions'],1);self.assertEqual(result['outcome'],'SAFE_YIELD')
 def test_unknown_cells_stop_before_save_preserving_enter_prefix(self):
  driver,result=self.graph(b'');self.assertEqual(len(driver.calls['execute']),1);self.assertEqual(result['completed_transitions'],1);self.assertEqual(result['outcome'],'SAFE_YIELD')
class SemanticGuardDiagnostic(unittest.TestCase):
 def test_existing_adapter_reuses_latest_semantics_at_admission(self):
  # Controlled diagnostic, no X11/input. This documents an uncovered boundary.
  from runtime.guarded_x11_v1.test_compiled import Bridge,spec,bindings,perceive,verify
  from runtime.guarded_x11_v1.compiled import _Adapter
  b=Bridge();a=_Adapter(b,spec(),bindings(),perceive,verify,lambda:False)
  observed=a.observe({});self.assertEqual(observed['predicates']['phase'],0)
  b.phase=2  # App semantic state changes after the read-only callback.
  request={'interface_id':a.interface['interface_id'],'session_scope':b.scope,
   'action':'enter','operation':'enter','symbol':a.interface['symbols']['field'],'observation':observed}
  admission=a.admit(request)
  self.assertTrue(admission['eligible'])
  self.assertEqual(observed['predicates']['phase'],0)
  self.assertEqual(b.phase,2);self.assertEqual(b.inputs,[])

if __name__=='__main__':unittest.main()
