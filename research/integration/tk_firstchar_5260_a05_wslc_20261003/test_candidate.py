import json
from pathlib import Path
import tempfile
import time
import unittest
from candidate import read_acknowledgement, send_payload, planned_rows


class AdmissionInputTests(unittest.TestCase):
    def test_refused_gate_has_no_key_or_save_emissions(self):
        effects=[]
        send_payload({'status':'REFUSED_NO_FOCUS_ACK'},'hxy',
                     lambda c: effects.append(c),lambda: effects.append('Save'),0,0)
        self.assertEqual(effects,[])

    def test_admitted_only_one_each(self):
        effects=[]
        send_payload({'status':'ADMITTED'},'hxy',
                     lambda c: effects.append(c),lambda: effects.append('Save'),0,0)
        self.assertEqual(effects,['h','x','y','Save'])

    def test_wrong_receipt_times_out_without_admission(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'focus_ack.json').write_text(json.dumps({'widget':'decoy'}))
            (root/'focus_state.json').write_text('{}')
            result=read_acknowledgement(root,{'token':'new','pid':17,
                'target_id':42,'ready_ns':1,'click_started_ns':2},2,50)
            self.assertEqual(result['status'],'REFUSED_NO_FOCUS_ACK')
            self.assertIsNone(result['ack'])

    def test_schedule_is_ten_balanced_fresh_rows(self):
        fixture={'seed':52605026,'replicates_per_cell':2}
        rows=planned_rows(fixture)
        self.assertEqual(len(rows),10)
        self.assertEqual(sum(r['mode']=='NOW_TARGET' for r in rows),4)
        self.assertEqual(sum(r['mode']=='ACK_TARGET' for r in rows),4)
        self.assertEqual(sum(r['mode']=='ACK_WRONG_TARGET' for r in rows),2)
        self.assertEqual(rows,planned_rows(fixture))


if __name__=='__main__': unittest.main()
