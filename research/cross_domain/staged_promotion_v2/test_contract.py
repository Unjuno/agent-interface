import tempfile,unittest
from pathlib import Path
from contract import Publisher
class T(unittest.TestCase):
    def test_naive_late_old_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);c=d/'c';a=d/'a';b=d/'b';a.write_bytes(b'A');b.write_bytes(b'B');p=Publisher(c,'naive',2);p.publish(b,generation=2,attempt_id='B');p.publish(a,generation=1,attempt_id='A');self.assertEqual(c.read_bytes(),b'A')
    def test_gate_rejects_stale(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);c=d/'c';a=d/'a';b=d/'b';a.write_bytes(b'A');b.write_bytes(b'B');p=Publisher(c,'generation_gate',2);p.publish(b,generation=2,attempt_id='B');r=p.publish(a,generation=1,attempt_id='A');self.assertEqual(c.read_bytes(),b'B');self.assertEqual(r['outcome'],'STALE_GENERATION');self.assertTrue(a.exists())
    def test_gate_refuses_future_too(self):
        with tempfile.TemporaryDirectory() as d:
            d=Path(d);c=d/'c';x=d/'x';x.write_bytes(b'X');p=Publisher(c,'generation_gate',2);r=p.publish(x,generation=3,attempt_id='X');self.assertFalse(r['eligible']);self.assertFalse(c.exists())
if __name__=='__main__':unittest.main()
