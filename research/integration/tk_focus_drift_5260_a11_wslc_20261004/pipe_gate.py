"""A09 bounded receipt gate; no input operations live here."""
import time
from pipe_receipt import admission_errors


def wait_for_target(session, binding, click_started_ns, timeout_ns=500_000_000,
                    poll_ns=1_000_000, max_age_ns=50_000_000):
    if any(type(value) is not int or value<=0 for value in (timeout_ns,poll_ns,max_age_ns)):
        raise ValueError('invalid gate bounds')
    started=time.monotonic_ns()
    deadline=started+timeout_ns
    samples=[]
    while True:
        session.drain()
        checked=time.monotonic_ns()
        latest=session.frames[-1] if session.frames else None
        state=latest['value'] if latest else None
        errors=admission_errors(state,binding,checked,click_started_ns,max_age_ns) if latest else ['no_frame']
        samples.append({'checked_ns':checked,'state':state,'seen_ns':latest['seen_ns'] if latest else None,
                        'errors':errors,'read_attempts':len(session.reads)})
        if not errors and checked<=deadline:
            return {'status':'ADMITTED','ack':state,'state':state,'samples':samples,
                    'started_ns':started,'decided_ns':checked,'deadline_ns':deadline,
                    'reason':'CURRENT_TARGET_RECEIPT'}
        if session.eof or checked>=deadline:
            return {'status':'REFUSED','ack':None,'state':state,'samples':samples,
                    'started_ns':started,'decided_ns':checked,'deadline_ns':deadline,
                    'reason':'EOF_BEFORE_ADMISSION' if session.eof else 'TIMEOUT'}
        time.sleep(min(poll_ns,deadline-checked)/1_000_000_000)
