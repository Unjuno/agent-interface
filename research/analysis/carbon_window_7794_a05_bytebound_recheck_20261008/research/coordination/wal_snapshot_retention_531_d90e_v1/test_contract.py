"""Offline tests. Never launches a writer, reader, GUI, or formal allocation."""
import copy,hashlib,json,unittest
from pathlib import Path
import audit
ROOT=Path(__file__).resolve().parent

class Contract(unittest.TestCase):
    def test_01_vendor_object(self):
        data=(ROOT/'vendor531.py').read_bytes()
        self.assertEqual(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),'24329aaedf166b98a5babf5cfb9c61af7c6f40f0')
    def test_02_schedule(self):
        p=json.loads((ROOT/'PLAN.json').read_text());cases=sum(p['batches'],[])
        self.assertEqual(len(cases),6);self.assertEqual(len({x['case'] for x in cases}),6)
        self.assertEqual(sum(x['milestones'][-1] for x in cases),768)
    def test_03_initial(self):
        v=audit.expected(0);self.assertEqual((v['generation'],v['retired']), (4,1))
        self.assertEqual([x['intent_seq'] for x in v['history']],[2,3])
    def test_04_final(self):
        v=audit.expected(128);self.assertEqual((v['generation'],v['retired']), (132,129))
        self.assertEqual([x['intent_seq'] for x in v['history']],[130,131])
    def test_05_boolean_not_integer(self):self.assertFalse(audit.same(0,False));self.assertFalse(audit.same(1,True))
    def test_06_empty_wal(self):self.assertEqual(audit.wal_info(b'')['valid_frames'],0)
    def test_07_short_wal(self):
        with self.assertRaises(ValueError):audit.wal_info(b'x'*31)
    def test_08_construction_wal(self):
        raw=(ROOT/'construction-00/c-HELD_TX/after-004/store.sqlite-wal').read_bytes()
        info=audit.wal_info(raw);self.assertEqual(info['valid_frames'],8);self.assertEqual(info['last_commit'],8)
    def test_09_changed_wal_payload(self):
        raw=bytearray((ROOT/'construction-00/c-HELD_TX/after-004/store.sqlite-wal').read_bytes());raw[-5]^=1
        with self.assertRaisesRegex(ValueError,'CHECKSUM'):audit.wal_info(bytes(raw))
    def test_10_read_db_with_wal(self):
        view=audit.restore_view(ROOT/'construction-00/c-HELD_TX/after-004');self.assertTrue(audit.same(view,audit.expected(4)))
    def test_11_copy_same_historical_view(self):
        views=[]
        for mode in ['HELD_TX','COPY_RELEASE']:
            row=json.loads((ROOT/f'construction-00/c-{mode}/ROW.json').read_text());views.append(row['reader_peek']['reported_view'])
        self.assertTrue(audit.same(*views))
    def test_12_denominator_rejected(self):
        errs,_,_=audit.check_rows([], [dict(case='absent')],[],filesystem=False,formal=False)
        self.assertIn('DENOMINATOR',errs)
if __name__=='__main__':unittest.main(verbosity=2)
