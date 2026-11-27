import unittest
from adapter import adapt_session_records

def sample(ns,kills):
    return {"scheduled_ns":ns,"sample_started_ns":ns,"sample_finished_ns":ns,
      "start_lateness_ns":0,"missed_periods_before":0,
      "payload":{"schema":"independent-progress-sample-v2","sample_ns":ns,
        "kill_count":kills,"death_count":0,"episode_finished":False,"player_dead":False,"map_exit":False},
      "controller_visible":False}

def event():
    return {"schema":"independent-progress-event-v2","event_sequence":1,"observed_ns":300,
      "kind":"KILL_COUNT_INCREASE","polarity":"positive","useful":True,"controller_visible":False,
      "before":{"kill_count":0},"after":{"kill_count":1,"delta":1}}

def row(kind,key,delivery=None):
    common={"key":key,"id":"program-a","step":0,"owner_id":"owner-a","intent_token":"intent-a"}
    if kind=="input_admission":
        return {"event":kind,**common,"admitted_ns":80,"input_ack_ns":85,"valid_until_ns":900}
    receipt={"event":"owner_explicit_keyup","operation":"up","key":key,"owner_id":"owner-a",
      "intent_token":"intent-a","valid_until_ns":900,"owner_keyrelease_started_ns":310,
      "owner_sync_returned_ns":320,"cancel_requested_after_sync":False,"server_sync_completed":True,
      "physical_verification_authoritative":False}
    return {"event":"input_release_transition","operation":"up",**common,"release_call_started_ns":305,
      "release_call_returned_ns":330,"owner_thread_keyup_receipt":receipt,
      "owner_thread_keyup_verified":True,"owner_thread_keyup_receipt_count":1,
      "owner_thread_keyup_history_complete":True,"owner_thread_keyup_verified_after_batch":True,
      "owner_transition_verified":True,"release_batch_schema":"input-release-batch-v3",
      "release_batch_identifier":"program-a","release_batch_step":0,"release_batch_size":1,
      "release_batch_position":0,"release_batch_delivery_position":delivery,
      "release_batch_complete":True,"physical_verification_authoritative":False}

class DeliveryBatchTests(unittest.TestCase):
    def test_separate_single_key_batches_within_one_program_are_not_merged(self):
        rows=[row("input_admission","space"),row("input_release_transition","space",0),
          row("input_admission","up"),row("input_release_transition","up",1)]
        result=adapt_session_records([sample(100,0),sample(300,1)],[event()],rows)
        self.assertEqual(result["trace_integrity"],"SOURCE_ROWS_JOINED")
        self.assertEqual(result["attributions"][0]["status"],"TEMPORALLY_UNIQUE")

    def test_two_member_batch_uses_local_and_delivery_positions(self):
        first=row("input_release_transition","space",0); first.update(release_batch_size=2,release_batch_position=0)
        second=row("input_release_transition","up",1); second.update(release_batch_size=2,release_batch_position=1)
        rows=[row("input_admission","space"),first,row("input_admission","up"),second]
        result=adapt_session_records([sample(100,0),sample(300,1)],[event()],rows)
        self.assertEqual(result["trace_integrity"],"SOURCE_ROWS_JOINED")
        self.assertEqual(result["attributions"][0]["status"],"TEMPORALLY_UNIQUE")

    def test_missing_delivery_position_fails_closed(self):
        rows=[row("input_admission","space"),row("input_release_transition","space",0),
              row("input_admission","up"),row("input_release_transition","up",2)]
        result=adapt_session_records([sample(100,0),sample(300,1)],[event()],rows)
        self.assertEqual(result["trace_integrity"],"HOLD_INCOMPLETE_RELEASE_BATCH")
        self.assertEqual(result["attributions"][0]["status"],"UNRESOLVED")

    def test_duplicate_delivery_position_fails_closed(self):
        rows=[row("input_admission","space"),row("input_release_transition","space",0),
              row("input_admission","up"),row("input_release_transition","up",0)]
        result=adapt_session_records([sample(100,0),sample(300,1)],[event()],rows)
        self.assertEqual(result["trace_integrity"],"HOLD_INCOMPLETE_RELEASE_BATCH")
        self.assertEqual(result["attributions"][0]["status"],"UNRESOLVED")

    def test_missing_member_in_delivery_batch_fails_closed(self):
        release=row("input_release_transition","space",0)
        release.update(release_batch_size=2,release_batch_position=0)
        rows=[row("input_admission","space"),release]
        result=adapt_session_records([sample(100,0),sample(300,1)],[event()],rows)
        self.assertEqual(result["trace_integrity"],"HOLD_INCOMPLETE_RELEASE_BATCH")
        self.assertEqual(result["attributions"][0]["status"],"UNRESOLVED")

    def test_mixed_legacy_and_delivery_positions_fail_closed(self):
        rows=[row("input_admission","space"),row("input_release_transition","space",0),
              row("input_admission","up"),row("input_release_transition","up",1)]
        rows[3].pop("release_batch_delivery_position")
        result=adapt_session_records([sample(100,0),sample(300,1)],[event()],rows)
        self.assertEqual(result["trace_integrity"],"HOLD_INCOMPLETE_RELEASE_BATCH")
        self.assertEqual(result["attributions"][0]["status"],"UNRESOLVED")

if __name__=='__main__': unittest.main()
