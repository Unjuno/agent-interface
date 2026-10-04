"""A11 preparation: validate observed drift, not authority for keyboard input."""
import copy
import time
def drift_errors(frames,binding,admitted_sequence,intervention_ns,checked_ns):
    if not isinstance(frames,(list,tuple)):return ['malformed']
    if not isinstance(binding,dict):return ['binding_types']
    if any(type(binding.get(k)) is not int or binding[k]<=0
           for k in ('pid','target_id')):return ['binding_types']
    if len(frames)!=2:return ['transition_count']
    errors=[]
    out,inside=frames
    try:
        if any(f.get('schema')!='issue5260-a09-focus-pipe-v1' or
               any(f.get(k)!=binding[k] for k in ('token','pid','target_id','freeze_sha256'))
               for f in frames):errors.append('binding')
        typed=[admitted_sequence,intervention_ns,checked_ns]
        typed.extend(f.get(k) for f in frames for k in
                     ('pid','target_id','sequence','event_ns','written_ns'))
        if any(type(v) is not int or v<=0 for v in typed):
            return errors+['types']
        if ((out.get('kind'),out.get('widget'))!=('FocusOut','target') or
            out.get('focus_get')!='other' or
            (inside.get('kind'),inside.get('widget'),inside.get('focus_get'))!=
            ('FocusIn','decoy','other')):errors.append('transition_kind')
        if not (admitted_sequence<out['sequence']<inside['sequence'] and
                intervention_ns<=out['event_ns']<=out['written_ns']<=
                inside['event_ns']<=inside['written_ns']<=checked_ns):
            errors.append('drift_order')
    except (KeyError,TypeError,AttributeError):errors.append('malformed')
    return errors


def wait_for_drift(session,binding,admitted_sequence,intervention_ns,
                   timeout_ns=500_000_000,poll_ns=1_000_000,max_age_ns=50_000_000):
    if any(type(v) is not int or v<=0 for v in
           (admitted_sequence,intervention_ns,timeout_ns,poll_ns,max_age_ns)):
        raise ValueError('invalid drift bounds')
    started=time.monotonic_ns()
    deadline=started+timeout_ns
    samples=[]
    while True:
        session.drain()
        checked=time.monotonic_ns()
        frames=[f['value'] for f in session.frames
                if type(f['value'].get('sequence')) is not int or
                f['value']['sequence']>admitted_sequence]
        errors=drift_errors(frames,binding,admitted_sequence,intervention_ns,checked)
        if not errors and checked-frames[-1]['written_ns']>max_age_ns:
            errors=['drift_expired']
        samples.append(dict(checked_ns=checked,frames=copy.deepcopy(frames),
                            errors=errors,read_attempts=len(session.reads)))
        reason=None
        if not errors and checked<=deadline:
            status='OBSERVED_DRIFT'
            reason='BOUND_TARGET_OUT_DECOY_IN'
        elif len(frames)>=2 and errors:
            status='STOP';reason='INVALID_TRANSITION'
        elif session.eof:
            status='STOP';reason='EOF'
        elif checked>=deadline:
            status='STOP';reason='TIMEOUT'
        if reason:
            return dict(status=status,reason=reason,frames=copy.deepcopy(frames),
                        samples=samples,started_ns=started,decided_ns=checked,
                        deadline_ns=deadline)
        time.sleep(min(poll_ns,deadline-checked)/1_000_000_000)


def dispatch(initial,arm,observed,payload,key,save):
    """Experimental stale control only; not a runtime safety interface.

    Caller owns obtaining/validating initial and observer result. Independent
    auditor must verify their provenance; arbitrary dictionaries are not authority.
    """
    if arm not in ('STABLE','DRIFT_STALE_CONTROL','DRIFT_REFUSE'):
        return dict(status='STOP',reason='UNKNOWN_ARM')
    if initial.get('status')!='ADMITTED':
        return dict(status='STOP',reason='INITIAL_NOT_ADMITTED')
    if arm!='STABLE':
        if observed.get('status')!='OBSERVED_DRIFT':
            return dict(status='STOP',reason='DRIFT_NOT_OBSERVED')
        if arm=='DRIFT_REFUSE':
            return dict(status='REFUSED',reason='OBSERVED_DRIFT')
    for char in payload:key(char)
    save()
    return dict(status='EMITTED',reason=arm)
