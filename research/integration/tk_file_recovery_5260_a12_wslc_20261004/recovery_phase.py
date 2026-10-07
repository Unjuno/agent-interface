"""A12 experimental three-arm phase wiring, not authenticated input authority."""
import time
from drift import wait_for_drift,dispatch
from recovery import RecoveryAttempt

def run_phase(gate,mode,session,binding,intervene,recover_click,payload,key,save,
              timeout_ns=500_000_000,poll_ns=1_000_000,max_age_ns=50_000_000):
    record={'prior':{'intervention':None,'drift':None},'recovery':None,
            'prior_emissions':{'keys':0,'saves':0}}
    prior=record['prior'];counts={'keys':0,'saves':0}
    def counted_key(char):
        counts['keys']+=1
        key(char)
    def counted_save():
        counts['saves']+=1
        save()
    if mode not in ('STABLE','DRIFT_REFUSE','DRIFT_RECOVER'):
        prior['dispatch']={'status':'STOP','reason':'UNKNOWN_ARM'}
        return record
    if gate.get('status')=='ADMITTED' and mode!='STABLE':
        prior['intervention']=intervene()
        prior['drift']=wait_for_drift(session,binding,gate['ack']['sequence'],
            prior['intervention']['started_ns'],timeout_ns,poll_ns,max_age_ns)
    prior['dispatch_started_ns']=time.monotonic_ns()
    prior['dispatch']=dispatch(gate,'STABLE' if mode=='STABLE' else 'DRIFT_REFUSE',
        prior['drift'],payload,counted_key,counted_save)
    prior['dispatch_completed_ns']=time.monotonic_ns()
    record['prior_emissions']=dict(counts)
    if mode=='DRIFT_RECOVER' and prior['dispatch']=={'status':'REFUSED','reason':'OBSERVED_DRIFT'}:
        record['recovery']=RecoveryAttempt().run(True,prior,counts['keys'],counts['saves'],
            session,binding,recover_click,payload,counted_key,counted_save,
            timeout_ns,poll_ns,max_age_ns)
    record['total_emissions']=dict(counts)
    return record
