"""A12 one explicit recovery attempt; experimental callback contract only.

Caller-supplied dictionaries are not authenticated authority. The independent
auditor must reconstruct all prior/refusal/recovery/input custody. This does
not eliminate the race between observing target focus and sending a key.
"""
import time
from pipe_gate import wait_for_target

class RecoveryAttempt:
    def __init__(self):
        self._attempted=False

    def run(self,requested,prior,prior_keys,prior_saves,session,binding,
            click,payload,key,save,timeout_ns=500_000_000,poll_ns=1_000_000,
            max_age_ns=50_000_000):
        if self._attempted:
            return dict(status='STOP',reason='RECOVERY_ALREADY_ATTEMPTED')
        if requested is not True:
            return dict(status='STOP',reason='NO_EXPLICIT_RECOVERY_REQUEST')
        if (type(prior_keys) is not int or type(prior_saves) is not int or
            prior_keys!=0 or prior_saves!=0):
            return dict(status='STOP',reason='PARTIAL_INPUT_NOT_RECOVERABLE')
        try:
            if (prior['dispatch']!={'status':'REFUSED','reason':'OBSERVED_DRIFT'} or
                prior['drift']['status']!='OBSERVED_DRIFT'):
                return dict(status='STOP',reason='NO_OBSERVED_DRIFT_REFUSAL')
            sequence=prior['drift']['frames'][-1]['sequence']
            if type(sequence) is not int or sequence<=0:
                return dict(status='STOP',reason='INVALID_DRIFT_SEQUENCE')
        except (KeyError,TypeError,IndexError):
            return dict(status='STOP',reason='MALFORMED_PRIOR')
        self._attempted=True
        record=dict(status='STOP',reason='RECOVERY_PENDING',requested=True,
                    started_ns=time.monotonic_ns(),prior_emissions={'keys':0,'saves':0})
        record['click']=click()
        clicked=record['click']
        if (clicked.get('widget')!='target' or
            any(type(clicked.get(k)) is not int or clicked[k]<=0 for k in ('started_ns','completed_ns')) or
            not record['started_ns']<=clicked['started_ns']<=clicked['completed_ns']):
            record['reason']='INVALID_RECOVERY_CLICK';return record
        gate=wait_for_target(session,binding,clicked['started_ns'],timeout_ns,poll_ns,max_age_ns)
        record['gate']=gate
        if gate['status']!='ADMITTED':
            record['reason']='RECOVERY_NOT_ADMITTED';return record
        if gate['ack']['sequence']<=sequence:
            record['reason']='RECOVERY_SEQUENCE_NOT_NEW';return record
        record['dispatch_started_ns']=time.monotonic_ns()
        for char in payload:key(char)
        save()
        record.update(status='EMITTED',reason='NEW_RECOVERY_ADMISSION',
                      dispatch_completed_ns=time.monotonic_ns())
        return record
