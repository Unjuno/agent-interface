import importlib.util, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('probe2',HERE/'probe_map01_recovery_mechanics_dev_v2.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)

def test_no_input_program():
    events=[{'event':'accepted','id':'wait-coast','intent_token':'c'}]
    row=probe.direct_bounds(events,'wait-coast')
    assert row['intent_token']=='c' and row['hold_count']==0

def test_intent_token_join():
    events=[
      {'event':'accepted','id':'wait-recovery','intent_token':'t'},
      {'event':'input_admission','intent_token':'t','key':'a','admitted_ns':100,'input_ack_ns':110},
      {'event':'input_release_transition','release_batch_identifier':'wait-recovery','intent_token':'t','key':'a','owner_transition_verified':True,'release_call_started_ns':210,'release_call_returned_ns':220},
    ]
    row=probe.direct_bounds(events,'wait-recovery')
    assert row['hold_count']==1
    assert abs(row['retained_lower_ms']-0.0001)<1e-12
    assert abs(row['retained_upper_ms']-0.00012)<1e-12

def test_program_id_is_not_required_on_admission():
    events=[
      {'event':'accepted','id':'wait-recovery','intent_token':'t'},
      {'event':'input_admission','intent_token':'t','key':'a','admitted_ns':1,'input_ack_ns':2},
      {'event':'input_release_transition','release_batch_identifier':'wait-recovery','intent_token':'t','key':'a','owner_transition_verified':True,'release_call_started_ns':3,'release_call_returned_ns':4},
    ]
    assert 'id' not in events[1]
    assert probe.direct_bounds(events,'wait-recovery')['hold_count']==1

def test_dev01_retained_timestamps_reconstruct():
    events=[
      {'event':'accepted','id':'wait-recovery','intent_token':'2520395d25be4e08ae711bdd07f28854'},
      {'event':'input_admission','intent_token':'2520395d25be4e08ae711bdd07f28854','key':'a','admitted_ns':182584497048,'input_ack_ns':182584752580},
      {'event':'input_release_transition','release_batch_identifier':'wait-recovery','intent_token':'2520395d25be4e08ae711bdd07f28854','key':'a','owner_transition_verified':True,'release_call_started_ns':182855234543,'release_call_returned_ns':182855497477},
    ]
    row=probe.direct_bounds(events,'wait-recovery')
    assert round(row['retained_lower_ms'],6)==270.481963
    assert round(row['retained_upper_ms'],6)==271.000429

def test_mismatched_token_fails_closed():
    events=[{'event':'accepted','id':'wait-recovery','intent_token':'t'},{'event':'input_admission','intent_token':'t','key':'a','admitted_ns':1,'input_ack_ns':2}]
    try: probe.direct_bounds(events,'wait-recovery')
    except AssertionError as exc: assert 'unmatched admission' in str(exc)
    else: raise AssertionError('missing release must fail')

if __name__=='__main__':
    tests=[v for k,v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:t()
    print(f'PASS {len(tests)} tests')
