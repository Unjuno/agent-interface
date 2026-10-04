import unittest
from adapter import adapt_session_records


def sample(ns, kills):
    return {
        "scheduled_ns": ns, "sample_started_ns": ns, "sample_finished_ns": ns,
        "start_lateness_ns": 0, "missed_periods_before": 0,
        "payload": {"schema":"independent-progress-sample-v2", "sample_ns":ns,
                    "kill_count":kills, "death_count":0, "episode_finished":False,
                    "player_dead":False, "map_exit":False},
        "controller_visible":False,
    }

def event(ns=300):
    return {"schema":"independent-progress-event-v2", "event_sequence":1,
            "observed_ns":ns, "kind":"KILL_COUNT_INCREASE", "polarity":"positive",
            "useful":True, "controller_visible":False,
            "before":{"kill_count":0}, "after":{"kill_count":1,"delta":1}}

def down(token="intent-a", identifier="plan-a", step=0, key="space", owner="owner-1"):
    return {"event":"input_admission", "key":key, "admitted_ns":80,
            "input_ack_ns":85, "valid_until_ns":900, "id":identifier,
            "step":step, "owner_id":owner, "intent_token":token}

def up(token="intent-a", identifier="plan-a", step=0, key="space", owner="owner-1",
       verified=True, sync_ns=320):
    receipt={"event":"owner_explicit_keyup", "operation":"up", "key":key,
             "owner_id":owner, "intent_token":token, "valid_until_ns":900,
             "owner_keyrelease_started_ns":310, "owner_sync_returned_ns":sync_ns,
             "cancel_requested_after_sync":False, "server_sync_completed":True,
             "physical_verification_authoritative":False}
    return {"event":"input_release_transition", "operation":"up", "key":key,
            "owner_id":owner, "intent_token":token, "id":identifier, "step":step,
            "release_call_started_ns":305, "release_call_returned_ns":330,
            "owner_thread_keyup_receipt":receipt,
            "owner_thread_keyup_verified":verified,
            "owner_thread_keyup_receipt_count":1,
            "owner_thread_keyup_history_complete":True,
            "owner_thread_keyup_verified_after_batch":verified,
            "owner_transition_verified":verified,
            "release_batch_schema":"input-release-batch-v3",
            "release_batch_identifier":"batch-"+identifier, "release_batch_step":step,
            "release_batch_size":1, "release_batch_position":0,
            "release_batch_complete":True,
            "physical_verification_authoritative":False}

class V15AttributionAdapterTests(unittest.TestCase):
    def setUp(self):
        self.samples=[sample(100,0),sample(300,1)]
        self.events=[event()]
        self.input=[down(),up()]

    def test_source_shaped_rows_produce_identity_bound_temporal_attribution(self):
        result=adapt_session_records(self.samples,self.events,self.input)
        row=result['attributions'][0]
        self.assertEqual(row['status'],'TEMPORALLY_UNIQUE')
        self.assertEqual(row['intent_token'],'intent-a')
        self.assertEqual(row['causal_attribution'],'NOT_ESTABLISHED')

    def test_overlapping_intent_tokens_remain_ambiguous(self):
        self.input.extend([down('intent-b','cover-b',key='a'),up('intent-b','cover-b',key='a')])
        result=adapt_session_records(self.samples,self.events,self.input)
        self.assertEqual(result['attributions'][0]['status'],'AMBIGUOUS')
        self.assertIsNone(result['attributions'][0]['intent_token'])

    def test_complete_multi_key_release_batch_stays_one_intent(self):
        second_down=down(key='Up')
        first_up=up()
        second_up=up(key='Up')
        first_up.update(release_batch_size=2,release_batch_position=0)
        second_up.update(release_batch_size=2,release_batch_position=1)
        self.input=[self.input[0],first_up,second_down,second_up]
        result=adapt_session_records(self.samples,self.events,self.input)
        self.assertEqual(result['attributions'][0]['status'],'TEMPORALLY_UNIQUE')
        self.assertEqual(result['attributions'][0]['intent_token'],'intent-a')

    def test_incomplete_release_batch_suppresses_unique_label(self):
        self.input[1]['release_batch_size']=2
        result=adapt_session_records(self.samples,self.events,self.input)
        self.assertEqual(result['attributions'][0]['status'],'UNRESOLVED')
        self.assertEqual(result['trace_integrity'],'HOLD_INCOMPLETE_RELEASE_BATCH')

    def test_unmatched_release_identity_cannot_make_input_look_complete(self):
        self.input[1]=up('intent-other','plan-other')
        result=adapt_session_records(self.samples,self.events,self.input)
        self.assertEqual(result['attributions'][0]['status'],'UNRESOLVED')
        self.assertEqual(result['attributions'][0]['causal_attribution'],'NOT_ESTABLISHED')

    def test_unverified_keyup_never_yields_unique_attribution(self):
        self.input[1]=up(verified=False)
        result=adapt_session_records(self.samples,self.events,self.input)
        self.assertEqual(result['attributions'][0]['status'],'UNRESOLVED')

    def test_event_outside_sample_stream_fails_closed(self):
        self.events=[event(301)]
        with self.assertRaises(ValueError):
            adapt_session_records(self.samples,self.events,self.input)

    def test_controller_visible_scorer_sample_is_rejected(self):
        self.samples[0]['controller_visible']=True
        with self.assertRaises(ValueError):
            adapt_session_records(self.samples,self.events,self.input)

    def test_admission_without_exact_intent_identity_cannot_be_labeled(self):
        self.input[0].pop('intent_token')
        result=adapt_session_records(self.samples,self.events,self.input)
        self.assertEqual(result['attributions'][0]['status'],'UNRESOLVED')
        self.assertEqual(result['trace_integrity'],'HOLD_UNBOUND_INPUT_IDENTITY')

if __name__=='__main__': unittest.main(verbosity=2)
