import unittest
from research.live_control.calc_ocr_graph_perception_v1 import make_perception, make_ocr_calc_method
from runtime.guarded_x11_v1.compiled import run
from runtime.guarded_x11_v1.test_compiled import Bridge

def tsv(value):
    return 'level\tconf\ttext\n5\t95\t'+value+'\n' if value is not None else ''

def graph():
    return make_ocr_calc_method(interface_id='calc',session_scope='private',surface='x11-window-20',sheet_handle='sheet',save_handle='save',confirm_handle='confirm')

def bindings():
    return {name:{'interaction':'click','offset':[2,2],'tail':[]} for name in ('enter','save','confirm')}

def contextual(native,image):
    phase=image.getpixel((0,0))[0]
    return ({'sheet_target_present':True,'save_target_present':True,'dialog_present':phase==2,'dialog_absent':phase!=2,'confirm_target_present':True,'saved_indication':phase>=3}, phase==0)

def verify(payload,native,image):
    return {'status':'succeeded','evidence_ref':payload['observation']['evidence_ref']}

class GraphPerceptionTests(unittest.TestCase):
    def test_composed_path_completes_when_blank_then_matching(self):
        b=Bridge()
        def ocr(native,image):
            return (tsv('641'),tsv('283')) if image.getpixel((0,0))[0]>0 else ('','')
        p=make_perception(contextual,ocr,expected=('641','283'))
        r=run(b,graph(),bindings(),perceive=p,verify_effect=verify)
        self.assertEqual(r['outcome'],'TASK_SUCCEEDED');self.assertEqual(len(b.inputs),3)
    def test_mismatch_after_entry_stops_without_save_or_replay(self):
        b=Bridge()
        def ocr(native,image):
            return (tsv('642'),tsv('283')) if image.getpixel((0,0))[0]>0 else ('','')
        r=run(b,graph(),bindings(),perceive=make_perception(contextual,ocr,expected=('641','283')),verify_effect=verify)
        self.assertEqual((r['outcome'],r['reason']),('SAFE_YIELD','effect_unavailable'))
        self.assertEqual(r['completed_transitions'],1);self.assertEqual(len(b.inputs),1)
        self.assertEqual(r['pending_effect']['action'],'enter')
    def test_conflicting_blank_and_ocr_does_not_start_entry(self):
        b=Bridge();p=make_perception(contextual,lambda n,i:(tsv('642'),tsv('283')),expected=('641','283'))
        r=run(b,graph(),bindings(),perceive=p,verify_effect=verify)
        self.assertEqual(r['outcome'],'SAFE_YIELD');self.assertEqual(b.inputs,[])
    def test_blank_change_at_input_guard_blocks_entry(self):
        b=Bridge();calls=[]
        def ocr(native,image):
            calls.append(1)
            return ('','') if len(calls)==1 else (tsv('642'),tsv('283'))
        r=run(b,graph(),bindings(),perceive=make_perception(contextual,ocr,expected=('641','283')),verify_effect=verify)
        self.assertEqual(b.inputs,[]);self.assertEqual(r['completed_transitions'],0)
        self.assertNotEqual(r['outcome'],'TASK_SUCCEEDED')
    def test_match_changes_at_save_guard_blocks_save(self):
        b=Bridge();phase_one_calls=[]
        def ocr(native,image):
            if image.getpixel((0,0))[0]==0: return ('','')
            phase_one_calls.append(1)
            return (tsv('641' if len(phase_one_calls)==1 else '642'),tsv('283'))
        r=run(b,graph(),bindings(),perceive=make_perception(contextual,ocr,expected=('641','283')),verify_effect=verify)
        self.assertEqual(len(b.inputs),1);self.assertEqual(r['completed_transitions'],1)
        self.assertNotEqual(r['outcome'],'TASK_SUCCEEDED')
    def test_matching_ocr_conflicts_with_blank_evidence(self):
        b=Bridge();p=make_perception(contextual,lambda n,i:(tsv('641'),tsv('283')),expected=('641','283'))
        r=run(b,graph(),bindings(),perceive=p,verify_effect=verify)
        self.assertEqual(r['outcome'],'SAFE_YIELD');self.assertEqual(b.inputs,[])
    def test_ocr_exception_does_not_turn_blank_evidence_into_entry(self):
        b=Bridge()
        def failed(native,image): raise TimeoutError('unavailable')
        r=run(b,graph(),bindings(),perceive=make_perception(contextual,failed,expected=('641','283')),verify_effect=verify)
        self.assertEqual(r['outcome'],'SAFE_YIELD');self.assertEqual(b.inputs,[])
    def test_reserved_predicate_cannot_be_overwritten_by_context(self):
        p=make_perception(lambda n,i:({'cells_match':False},True),lambda n,i:('',''),expected=('641','283'))
        with self.assertRaises(ValueError):p({},None)
if __name__=='__main__':unittest.main()
