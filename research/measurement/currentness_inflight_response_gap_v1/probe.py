from candidate_copy import Scope, DecisionRequest, Invalidation, EpochBarrier
s=Scope('session','target')
b=EpochBarrier()
request_started_epoch=b.epoch.get(s,0)
assert request_started_epoch==0
inv=b.invalidate(Invalidation('inv-1',s))
assert inv['epoch']==1
install=b.install(DecisionRequest('late-response',s,100))
use=b.try_use(s,'late-response')
result={
 'request_started_epoch':request_started_epoch,
 'current_epoch_after_invalidation':b.epoch[s],
 'decision_stamped_epoch':install['epoch'],
 'try_use_status':use['status'],
 'decision':'FAIL_INFLIGHT_STALE_RESPONSE_LAUNDERED' if request_started_epoch < b.epoch[s] and use['status']=='ADMITTED' else 'HOLD_PREDECESSOR_ALREADY_BINDS_ORIGIN'
}
print(result)
assert result['decision']=='FAIL_INFLIGHT_STALE_RESPONSE_LAUNDERED'
