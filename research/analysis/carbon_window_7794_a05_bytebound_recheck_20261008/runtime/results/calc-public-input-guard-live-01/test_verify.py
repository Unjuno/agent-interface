"""Semantic mutations bypass the immutable-file checksum layer deliberately."""
import base64,copy,hashlib,io,json,unittest
from pathlib import Path
from PIL import Image
import openpyxl
from verify import audit,ORIGINAL
ROOT=Path(__file__).resolve().parent
class RetainedAuditTests(unittest.TestCase):
 def setUp(self):self.overlay={}
 def read(self,relative):return self.overlay.get(str(relative),(ROOT/relative).read_bytes())
 def mutate(self,path,fn):
  d=json.loads((ROOT/path).read_text());fn(d);self.overlay[path]=(json.dumps(d,indent=2)+'\n').encode()
 def rejected(self,message):
  with self.assertRaisesRegex(ValueError,message):audit(ROOT,read=self.read,verify_manifest=False)
 def bridge(self,case='compiled-normal'):return next((ROOT/case/'public-owner').glob('guarded-session-*')).relative_to(ROOT).as_posix()
 def test_unmodified_complete_bundle_passes(self):self.assertEqual(audit(ROOT)['status'],'PASS')
 def test_wrong_control_claiming_save_is_rejected(self):
  bridge=self.bridge('compiled-wrong');f=next((ROOT/bridge).glob('program-*.json')).relative_to(ROOT).as_posix()
  self.mutate(f,lambda d:d['ops'].insert(1,{'op':'key_chord','keys':['CTRL','s']}));self.rejected('Save request count changed')
 def test_true_task_verdict_cannot_replace_modal_yield(self):
  self.mutate('compiled-normal/replies/009.json',lambda d:d['raw']['method_receipt'].update(outcome='TASK_SUCCEEDED'));self.rejected('raw terminal relabeled')
 def test_lost_completed_prefix_is_rejected(self):
  self.mutate('compiled-wrong/replies/009.json',lambda d:d['raw']['method_receipt'].update(completed_transitions=0));self.rejected('completed prefix')
 def test_ocr_from_other_sequence_is_rejected(self):
  self.mutate('compiled-normal/method/ocr/002.json',lambda d:d.update(sequence=10));self.rejected('OCR source mismatch')
 def test_ocr_glyphs_must_match_claimed_values(self):
  p='compiled-normal/method/ocr/002.tsv';self.overlay[p]=(ROOT/p).read_bytes().replace(b'864',b'863');self.rejected('OCR glyph evidence')
 def test_missing_pre_s_key_guard_is_rejected(self):
  self.mutate('compiled-normal/method/guard-events.json',lambda d:d.pop());self.rejected('guard dependency changed')
 def test_guard_checked_changed_cell_pixels_is_rejected(self):
  path=self.bridge()+'/observation-15.json';native=json.loads((ROOT/path).read_text());artifact=native['native']['artifact'];relative=Path(artifact['path']).relative_to(ORIGINAL).as_posix()
  rgb=Image.open(ROOT/relative).convert('RGB');rgb.putpixel((92,205),(255,0,0));buf=io.BytesIO();rgb.save(buf,format='PNG');data=buf.getvalue();self.overlay[relative]=data
  self.mutate(path,lambda d:d['native']['artifact'].update(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data)))
  self.rejected('Save cell dependency pixels changed')
 def test_presented_base64_must_be_exact_source(self):
  self.mutate('compiled-normal/replies/009.json',lambda d:d['feedback']['image'].update(data=base64.b64encode(b'not original PNG').decode()));self.rejected('presented image bytes')
 def test_mismatched_final_observation_cannot_deliver_feedback(self):
  self.mutate('compiled-normal/replies/009.json',lambda d:d['raw']['method_receipt']['observations'][-1].update(sequence=15));self.rejected('method observation/source')
 def test_input_neutral_release_is_required(self):
  bridge=self.bridge();p=next((ROOT/bridge).glob('public-dispatch-*.json')).relative_to(ROOT).as_posix()
  self.mutate(p,lambda d:d['result']['execution']['releases'][0].update(keys_down=['CTRL']));self.rejected('program neutral release')
 def test_same_owner_close_release_is_required(self):
  self.mutate('compiled-normal/close.json',lambda d:d['release'].update(verified=False));self.rejected('same-owner close/release')
 def test_cleanup_cannot_hide_remaining_process(self):
  self.mutate('compiled-normal/cleanup.json',lambda d:d.update(remaining=[123]));self.rejected('owned child remains')
 def test_post_terminal_score_must_follow_original_owner(self):
  self.mutate('compiled-normal/post-terminal-score.json',lambda d:d.update(original_owner_and_children_absent=False));self.rejected('post-terminal boundary')
 def test_bad_saved_value_is_rejected_even_with_consistent_hashes(self):
  p='compiled-normal/saved.xlsx';book=openpyxl.load_workbook(ROOT/p);book.active['A2']=863;buf=io.BytesIO();book.save(buf);data=buf.getvalue()
  self.overlay[p]=data;self.overlay['compiled-normal/primary-values.xlsx']=data
  self.mutate('compiled-normal/post-terminal-score.json',lambda d:d.update(source_sha256=hashlib.sha256(data).hexdigest(),nonempty_cells={'A1':731,'A2':863}))
  self.rejected('independent saved cells')
 def test_cumulative_counters_cannot_replace_program_counts(self):
  bridge=self.bridge();p=next((ROOT/bridge).glob('public-dispatch-*.json')).relative_to(ROOT).as_posix()
  self.mutate(p,lambda d:d['result']['execution'].pop('program_emissions'))
  with self.assertRaises((ValueError,KeyError)):audit(ROOT,read=self.read,verify_manifest=False)
 def test_expired_program_lease_is_rejected(self):
  bridge=self.bridge();f=next((ROOT/bridge).glob('program-*.json')).relative_to(ROOT).as_posix();self.mutate(f,lambda d:d['authority'].update(expires_at_ns=1));self.rejected('recorded lease')
 def test_program_scope_cannot_be_rebound(self):
  bridge=self.bridge();f=next((ROOT/bridge).glob('program-*.json')).relative_to(ROOT).as_posix();self.mutate(f,lambda d:d['authority'].update(lease_id='different-scope'));self.rejected('program scope changed')
 def public_guard_result(self):
  for f in (ROOT/self.bridge()).glob('result-*.json'):
   if 'additional_input_checks' in json.loads(f.read_text()):return f.relative_to(ROOT).as_posix()
  raise ValueError('missing public input guard result')
 def test_public_guard_cannot_claim_failed_check_eligible(self):
  self.mutate(self.public_guard_result(),lambda d:d['additional_input_checks'][0].update(eligible=False));self.rejected('public input guard evidence')
 def test_public_guard_cannot_omit_before_s_check(self):
  self.mutate(self.public_guard_result(),lambda d:d['additional_input_checks'].pop());self.rejected('public input guard stages')
 def test_public_guard_scope_cannot_be_rebound(self):
  self.mutate(self.public_guard_result(),lambda d:d['additional_input_checks'][0].update(scope='foreign'));self.rejected('public input guard scope')
 def test_public_guard_must_follow_current_capture(self):
  self.mutate(self.public_guard_result(),lambda d:d['additional_input_checks'][0].update(started_ns=1));self.rejected('public input guard timing/source')
if __name__=='__main__':unittest.main()
