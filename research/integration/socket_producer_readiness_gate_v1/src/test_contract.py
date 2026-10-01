import json,subprocess,tempfile,unittest
from pathlib import Path
from run_case import run_case,READ_TIMEOUT_S,PRODUCER_DELAY_S

HERE=Path(__file__).resolve().parents[1];UP=HERE/'upstream'
EXPECTED_BLOBS={
 'event_socket_v11.py':'fe71be94c9284af0ae7c0b4db0b47dd8b1a86522',
 'event_cursor_v5.py':'924979d24611601c4595c1f412fb75cdc413e444',
 'event_scope.py':'d5fc49ce4bf595426adfc833650c3f2641913c94',
 'request_boundary_v2.py':'6e4be1e8a6c7829f91258fd88f6243bbd799adab',
 'command_once_v2.py':'40a24130e5f8f2bd9b54536d5468b73b2abe908d',
 'bounded_pipe_writer_v2.py':'8dbace5de64bcf4699f43365b42a42166645c7d4',
}
class Contract(unittest.TestCase):
 def test_exact_upstream_git_blobs(self):
  for name,want in EXPECTED_BLOBS.items():
   got=subprocess.check_output(['git','hash-object',str(UP/name)],text=True).strip();self.assertEqual(got,want,name)
 def test_timing_factor_frozen(self):
  self.assertEqual(READ_TIMEOUT_S,0.05);self.assertEqual(PRODUCER_DELAY_S,0.15);self.assertGreater(PRODUCER_DELAY_S,READ_TIMEOUT_S)
 def test_endpoint_only_exposes_timeout(self):
  with tempfile.TemporaryDirectory() as d:
   r=run_case(Path(d)/'x','excluded-baseline','endpoint_only','action')
   self.assertEqual(r['status'],'timeout');self.assertEqual(r['record_count'],0);self.assertEqual(r['response_authority'],'none')
 def test_first_record_gate_reaches_boundary(self):
  with tempfile.TemporaryDirectory() as d:
   r=run_case(Path(d)/'x','excluded-candidate','first_record_gate','request')
   self.assertEqual(r['status'],'boundary');self.assertEqual(r['record_count'],1);self.assertEqual(r['response_authority'],'none')
   self.assertLessEqual(r['first_record_appended_ns'],r['endpoint_published_ns']);self.assertEqual(r['socket_readiness'],'first_record_appended')
 def test_silent_never_ready(self):
  with tempfile.TemporaryDirectory() as d:
   r=run_case(Path(d)/'x','excluded-silent','first_record_gate','action','silent')
   self.assertEqual(r['socket_event'],'observation_socket_unready');self.assertIsNone(r['status']);self.assertEqual(r['record_count'],0);self.assertEqual(r['socket_authority'],'none')
 def test_malformed_never_ready(self):
  with tempfile.TemporaryDirectory() as d:
   r=run_case(Path(d)/'x','excluded-malformed','first_record_gate','action','malformed')
   self.assertEqual(r['socket_event'],'observation_socket_unready');self.assertIsNone(r['status']);self.assertEqual(r['record_count'],0);self.assertEqual(r['socket_authority'],'none');self.assertNotEqual(r['server_code'],0)
if __name__=='__main__':unittest.main()
