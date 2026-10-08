from collections import Counter
import unittest
import candidate


class CandidateTests(unittest.TestCase):
    def test_schedule_has_ten_fresh_apps_with_common_instrumentation(self):
        rows=candidate.planned_rows({'seed':52609026,'replicates_per_cell':2})
        self.assertEqual(len(rows),10)
        self.assertEqual(Counter((row['mode'],row['load']) for row in rows),{
            ('NOW_TARGET','idle'):2,('NOW_TARGET','cpu_busy'):2,
            ('PIPE_ACK_TARGET','idle'):2,('PIPE_ACK_TARGET','cpu_busy'):2,
            ('PIPE_ACK_WRONG_TARGET','idle'):1,('PIPE_ACK_WRONG_TARGET','cpu_busy'):1})
        self.assertEqual({row['instrumentation_mode'] for row in rows},{'MEMORY_ONLY'})

    def test_refused_gate_does_not_call_any_input_operation(self):
        calls=[]
        candidate.send_payload({'status':'REFUSED'},'hxy',calls.append,
                               lambda:calls.append('Save'),0,0)
        self.assertEqual(calls,[])

    def test_wrong_target_decoy_geometry_is_checked_before_xlib_import(self):
        self.assertTrue(hasattr(candidate,'click_geometry'))
        ready={'geometry':{'target_root_x':1,'target_root_y':1,'target_width':10,
            'target_height':10,'save_root_x':1,'save_root_y':1,'save_width':10,'save_height':10}}
        with self.assertRaises(RuntimeError):candidate.click_geometry(ready,{'mode':'PIPE_ACK_WRONG_TARGET','instrumentation_mode':'MEMORY_ONLY'})


if __name__=='__main__':unittest.main()
