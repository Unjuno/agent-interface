import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('probe',HERE/'probe_map01_recovery_mechanics_dev_v1.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)

def test_direct_none():
    out=probe.direct_bounds([], 'coast')
    assert out['hold_count']==0 and out['retained_lower_ms']==0 and out['retained_upper_ms']==0

def test_direct_one_key_interval():
    events=[
      {'event':'input_admission','id':'recovery','intent_token':'t','key':'a','admitted_ns':100,'input_ack_ns':110},
      {'event':'input_release_transition','release_batch_identifier':'recovery','intent_token':'t','key':'a','owner_transition_verified':True,'release_call_started_ns':210,'release_call_returned_ns':220},
    ]
    out=probe.direct_bounds(events,'recovery')
    assert abs(out['retained_lower_ms']-0.0001)<1e-12
    assert abs(out['retained_upper_ms']-0.00012)<1e-12

def test_unmatched_release_fails_closed():
    try:
        probe.direct_bounds([{'event':'input_admission','id':'recovery','intent_token':'t','key':'a','admitted_ns':1,'input_ack_ns':2}],'recovery')
    except AssertionError as exc:
        assert 'unmatched admission' in str(exc)
    else:
        raise AssertionError('unmatched admission must fail')

if __name__=='__main__':
    tests=(test_direct_none,test_direct_one_key_interval,test_unmatched_release_fails_closed)
    for test in tests:test()
    print(f'PASS {len(tests)} tests')
