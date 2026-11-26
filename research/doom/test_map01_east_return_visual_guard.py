"""The east-return gate only authorizes a fresh bound image comparison."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from map01_east_return_visual_guard import check

class EastReturnVisualGuardTests(unittest.TestCase):
 def test_bound_cross_frame_compares_reference_and_rejects_other_scene(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);ref=root/'ref.png';frame=root/'frame.png'
   Image.new('RGB',(1280,800),(30,60,90)).save(ref)
   Image.new('RGB',(1280,800),(30,60,90)).save(frame)
   sha=hashlib.sha256(ref.read_bytes()).hexdigest()
   def source():
    with Image.open(frame) as image:rgb=hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()
    return {'event':'observation','id':'reverse-cross','step':0,'sequence':4,'capture_ns':100,'image':str(frame),
      'frame_rgb_sha256':rgb,'pointer_binding':{'surface':7,'focus':7,'geometry':[321,180,640,480]},
      'input_focus_before':7,'input_focus_after':7,'exact':True,'focus_samples_match':True,
      'renewal_owner_id':'owner','input_owner_generation':3,
      'target_process_identity':{'sequence':4,'surface':7,'digest':'proc'},
      'target_renewal_window_identity':{'sequence':4,'surface':7,'digest':'window'}}
   terminal={'event':'terminal','id':'reverse-cross','status':'completed','terminal_ns':150,'input_owner_id':'owner','input_owner_generation':3,'release':{'verified':True,'keys_down':[],'buttons_down':[],'keys_unknown':[],'key_state_errors':[],'intent_token':'token'}}
   transition={'event':'input_release_transition','id':'reverse-cross','operation':'up','key':'Up','owner_id':'owner','intent_token':'token','owner_transition_verified':True,'admission_receipt_valid':True,'release_batch_complete':True,'owner_sample_ordered_after_batch':True,'owner_identity_matches_after_batch':True,'intent_token_matches_after_batch':True,'owned_keycodes_after_batch':[],'owner_thread_keyup_verified_after_batch':True,'owner_sample_after_finished_ns':90,'owner_thread_keyup_receipt':{'server_keyup_verified':True,'owner_keymap_sampled_ns':85,'owner_id':'owner','intent_token':'token','key':'Up'}}
   settlement={'event':'door_settle','operation_id':'reverse-cross','status':'DONE','emit_ns':160}
   expected={'owner':'owner','generation':3,'surface':7,'process_digest':'proc','window_digest':'window','sequence':4,'geometry':[321,180,640,480]}
   typed=source();typed['event']='typed_observation';typed.pop('image')
   kwargs={'typed':typed,'reference':ref,'reference_sha256':sha,'runtime_dir':root,'clock':lambda:200,'terminal':terminal,'transition':transition,'settlement':settlement,'expected':expected}
   receipt=check(source(),**kwargs)
   self.assertTrue(receipt['passed']);self.assertEqual(receipt['sequence'],4)
   Image.new('RGB',(1280,800),(240,240,240)).save(frame)
   other=source();other_typed=dict(typed,frame_rgb_sha256=other['frame_rgb_sha256'])
   self.assertFalse(check(other,**dict(kwargs,typed=other_typed))['passed'])
   with self.assertRaises(ValueError):check(other,**kwargs)
   # Restore a valid pair so each negative reaches the intended check.
   Image.new('RGB',(1280,800),(30,60,90)).save(frame)
   typed=source();typed['event']='typed_observation';typed.pop('image');kwargs['typed']=typed
   early=source();early['capture_ns']=80;early_typed=dict(typed,capture_ns=80)
   with self.assertRaisesRegex(ValueError,'post-release'):check(early,**dict(kwargs,typed=early_typed))
   wrong=source();wrong['sequence']=3;wrong['target_process_identity']['sequence']=3;wrong['target_renewal_window_identity']['sequence']=3
   wrong_typed=dict(typed,sequence=3,target_process_identity=wrong['target_process_identity'],target_renewal_window_identity=wrong['target_renewal_window_identity'])
   with self.assertRaisesRegex(ValueError,'evidence differs'):check(wrong,**dict(kwargs,typed=wrong_typed))
   wrong=source();wrong['pointer_binding']['geometry']=[1,2,320,240]
   wrong_typed=dict(typed,pointer_binding=wrong['pointer_binding'])
   with self.assertRaisesRegex(ValueError,'binding differs'):check(wrong,**dict(kwargs,typed=wrong_typed))
   bad_transition=dict(transition,release_batch_complete=False)
   with self.assertRaisesRegex(ValueError,'evidence differs'):check(source(),**dict(kwargs,transition=bad_transition))
   wrong_expected=dict(expected,process_digest=None)
   wrong=source();wrong['target_process_identity']['digest']=None
   wrong_typed=dict(typed,target_process_identity=wrong['target_process_identity'])
   with self.assertRaisesRegex(ValueError,'evidence differs'):check(wrong,**dict(kwargs,expected=wrong_expected,typed=wrong_typed))
   invalid=source();invalid['id']='reverse-turn-3'
   with self.assertRaisesRegex(ValueError,'wrong observation'):check(invalid,**kwargs)
   with self.assertRaisesRegex(ValueError,'reference digest'):check(source(),**dict(kwargs,reference_sha256='0'*64))
   with self.assertRaisesRegex(ValueError,'stale'):check(source(),**dict(kwargs,clock=lambda:2_000_000_100))
   bad_typed=dict(typed,step=False)
   with self.assertRaisesRegex(ValueError,'typed and full'):check(source(),**dict(kwargs,typed=bad_typed))
   missing=source();missing.pop('step');missing_typed=dict(typed);missing_typed.pop('step')
   with self.assertRaisesRegex(ValueError,'wrong observation'):check(missing,**dict(kwargs,typed=missing_typed))
if __name__=='__main__':unittest.main()
