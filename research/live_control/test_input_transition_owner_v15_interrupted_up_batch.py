"""Target invalidation racing a queued UP; deterministic fake owner."""
import threading,time,unittest
from input_transition_owner_v4 import InputOwner
from test_input_transition_owner_v15_cleanup_lease_identity import DeferredOwner,Lease

class InterruptedUpBatchTests(unittest.TestCase):
 def run_case(self, mutate=None):
  owner=InputOwner(":fake",_owner_cls=DeferredOwner);lease=Lease("intent");result=[]
  lease.target_process_identity=(1,41,"a"*64,lease.deadline)
  lease.interruption_snapshot=lambda: ({"intent_token":lease.intent_token,"record":lease.interruptions[0]} if lease.interruptions else None)
  def run():
   try: result.append(owner.call("up_batch",lease,["W"]))
   except BaseException as e:result.append(e)
  owner.call("down",lease,"W");worker=threading.Thread(target=run);worker.start()
  try:
   self.assertTrue(owner._inner.batch_entered.wait(1))
   row={"event":"owner_release","reason":"target_generation_invalidated","verified":True,
    "keys_down":[],"buttons_down":[],"keys_unknown":[],"key_state_errors":[],
    "verified_ns":time.perf_counter_ns(),"valid_until_ns":lease.deadline,"intent_token":lease.intent_token,
    "target_process_identity":list(lease.target_process_identity),
    "target_process_identity_reader":{"retired":True},"key_release_attempts":{"38":{"verified":True,
     "attempts":[{"attempt":1,"keyrelease_started_ns":10,"sync_returned_ns":11,"keymap_sampled_ns":12,
                  "server_key_down_before":True,"server_key_down_after":False}]}}}
   if mutate:mutate(row)
   owner._inner.records.append(row);lease.record_interruption(row);owner._inner.allow_batch_error.set();worker.join(2)
   self.assertFalse(worker.is_alive());self.assertEqual(len(result),1);return result[0]
  finally:
   owner._inner.allow_batch_error.set();worker.join(2);owner.close()
 def test_exact_verified_interruption_joins_cleanup_without_claiming_explicit_up(self):
  result=self.run_case();self.assertIsInstance(result,list);self.assertFalse(result[0]["ordinary_release_candidate"])
  self.assertTrue(result[0]["owner_cleanup_release_verified"]);self.assertFalse(result[0]["owner_thread_keyup_verified"])
 def test_wrong_token_and_unverified_key_are_not_joined(self):
  for mutate in (lambda r:r.update(intent_token="other"),lambda r:r["key_release_attempts"]["38"].update(verified=False)):
   with self.subTest(mutate=mutate):self.assertIsInstance(self.run_case(mutate),ValueError)
if __name__=="__main__":unittest.main()
