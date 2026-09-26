"""Read-only interval certificate; it never grants input or task-success authority."""
from __future__ import annotations

def estimate(samples: list[dict], context: dict, keycode: int, deadline_ns: int) -> dict:
    unknown={'status':'UNKNOWN','authority':'none','task_success':False,'interval_ns':None}
    if not samples:return dict(unknown,reason='no_samples')
    state=[];last_end=-1
    try:
        if type(keycode) is not int or not 8<=keycode<=255:raise ValueError('keycode')
        for i,r in enumerate(samples):
            if any(r.get(k)!=v for k,v in context.items()):raise ValueError('identity')
            if r['keycode']!=keycode or type(r['sequence']) is not int or r['sequence']!=i:raise ValueError('sequence_key')
            a,z=r['start_ns'],r['end_ns']
            if type(a) is not int or type(z) is not int or not 0<=a<=z or a<last_end:raise ValueError('clock_order')
            last_end=z;bits=bytes.fromhex(r['bitmap_hex'])
            if len(bits)!=32:raise ValueError('bitmap_size')
            state.append(bool(bits[keycode//8]&(1<<(keycode%8))))
        if state[0]:raise ValueError('initial_not_neutral')
        first_down=state.index(True)
        first_up=state.index(False,first_down+1)
        if any(state[first_up:]):raise ValueError('multiple_holds')
        lo=samples[first_up-1]['start_ns'];hi=samples[first_up]['end_ns']
        return {'status':'WITHIN_BOUND' if hi<=deadline_ns else 'UNRESOLVED_BOUND',
                'authority':'none','task_success':False,'interval_ns':[lo,hi],
                'last_down_sequence':first_up-1,'first_up_sequence':first_up,
                'reason':'sampled_logical_release_upper_bound_not_exact_event_time'}
    except (ValueError,KeyError,TypeError,IndexError) as e:return dict(unknown,reason=str(e))
