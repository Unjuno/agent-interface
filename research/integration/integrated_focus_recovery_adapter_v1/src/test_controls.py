from runner import FakeClient
from adapter import execute_with_policy,RecoveryRejected

task={'task_id':'neg','token':'t'}; aliases={'field':'f','submit':'s'}
c=FakeClient(terminal_reason='lease_expired')
r=execute_with_policy(c,task,aliases,'focus_recovery_adapter')
assert r['recovery_queries']==0 and r['result']['reason']=='execution_failed'
for bad in [
 {'focus':'B','surface':'B','geometry':[1,2,3,4],'authority':'task','task_input_granted':False},
 {'focus':'B','surface':'B','geometry':[1,2,3,4],'authority':'none','task_input_granted':True},
 {'focus':'A','surface':'A','geometry':[1,2,3,4],'authority':'none','task_input_granted':False},
]:
 c=FakeClient(recovery=bad)
 try: execute_with_policy(c,task,aliases,'focus_recovery_adapter')
 except RecoveryRejected: pass
 else: raise AssertionError(bad)
print('controls PASS')
