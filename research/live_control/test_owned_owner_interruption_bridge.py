"""Explicitly bound remote interruption propagation; no real X."""
import copy,threading,time,unittest
from types import SimpleNamespace as NS
from lease_cause_v2 import Lease
from input_owner_service_adapter import OwnedOwnerAdapter
import input_owner_rpc_v2 as rpc

class BridgeTests(unittest.TestCase):
 def setUp(self):
  self.lease=Lease(time.perf_counter_ns()+10_000_000_000);self.lease.expected_focus=self.lease.expected_surface=41
  self.lease.expected_geometry=[0,0,32,32];self.lease.target_process_identity=(1,41,"a"*64,self.lease.deadline)
  self.owner=OwnedOwnerAdapter.__new__(OwnedOwnerAdapter);self.owner._lock=threading.RLock();self.owner._obligation=None;self.owner._records=[]
  self.owner._attempted=set();self.owner._leases={self.lease.intent_token:self.lease};self.owner._bindings={self.lease.intent_token:rpc.encode_lease(self.lease)}
  self.owner._closed=False;self.owner.control=NS(outcomes={});self.owner.owner_id="owner";self.owner.service_id="service"
  attempt={"attempt":1,"keyrelease_started_ns":10,"sync_returned_ns":11,"keymap_sampled_ns":12,"server_key_down_before":True,"server_key_down_after":False}
  self.record={"event":"owner_release","reason":"target_generation_invalidated","intent_token":self.lease.intent_token,
   "valid_until_ns":self.lease.deadline,"verified_ns":20,"target_process_identity":list(self.lease.target_process_identity),"verified":True,
   "keys_down":[],"buttons_down":[],"keys_unknown":[],"key_state_errors":[],"key_state_source":"x11_query_keymap",
   "target_process_identity_reader":{"retired":True},"key_release_attempts":{"111":{"verified":True,"attempts":[attempt]},"50":{"verified":True,"attempts":[attempt]}}}
  self.rows=[{"key":key,"owner_id":"owner","intent_token":self.lease.intent_token,"valid_until_ns":self.lease.deadline,
   "owner_interruption_cleanup_join":True,"owner_cleanup_release_verified":True,"ordinary_release_candidate":False,
   "owner_cleanup_record":copy.deepcopy(self.record),"owner_cleanup_keycode":{"Up":111,"Shift_L":50}[key],"admission_receipt_valid":True,
   "admission_receipt":{"event":"input_admission","key":key,"keycode":{"Up":111,"Shift_L":50}[key],
                        "owner_id":"owner","intent_token":self.lease.intent_token,"valid_until_ns":self.lease.deadline,
                        "admitted_ns":1,"input_ack_ns":2}}
   for key in ["Up","Shift_L"]]
  self.owner.client=NS(records=[copy.deepcopy(self.record)],call=lambda *a,**k:copy.deepcopy(self.rows))
 def test_valid_bound_remote_cause_reaches_original_lease(self):
  self.owner.call("up_batch",self.lease,["Up","Shift_L"])
  self.assertEqual(self.lease.interruption_snapshot(),{"intent_token":self.lease.intent_token,"record":self.record})
  self.assertIsNone(self.owner.obligation_snapshot())
 def test_cause_not_in_remote_history_fails_closed(self):
  self.owner.client.records=[]
  with self.assertRaises(ValueError):self.owner.call("up_batch",self.lease,["Up","Shift_L"])
  self.assertIsNone(self.lease.interruption_snapshot());self.assertIsNotNone(self.owner.obligation_snapshot())
 def test_two_keys_cannot_reuse_one_cleanup_keycode(self):
  self.rows[1]["owner_cleanup_keycode"]=111
  with self.assertRaises(ValueError):self.owner.call("up_batch",self.lease,["Up","Shift_L"])
  self.assertIsNone(self.lease.interruption_snapshot());self.assertIsNotNone(self.owner.obligation_snapshot())
 def test_release_predating_admission_fails_closed(self):
  self.rows[0]["admission_receipt"]["input_ack_ns"]=15
  with self.assertRaises(ValueError):self.owner.call("up_batch",self.lease,["Up","Shift_L"])
  self.assertIsNone(self.lease.interruption_snapshot());self.assertIsNotNone(self.owner.obligation_snapshot())
 def test_mismatched_source_fails_closed(self):
  for row in self.rows:row["owner_cleanup_record"]["target_process_identity"][2]="b"*64
  self.owner.client.records=[copy.deepcopy(self.rows[0]["owner_cleanup_record"])]
  with self.assertRaises(ValueError):self.owner.call("up_batch",self.lease,["Up","Shift_L"])
  self.assertIsNone(self.lease.interruption_snapshot());self.assertIsNotNone(self.owner.obligation_snapshot())
if __name__=="__main__":unittest.main()
