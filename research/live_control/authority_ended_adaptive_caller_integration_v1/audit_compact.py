import json,sys
from pathlib import Path
r=json.loads((Path(sys.argv[1])/'formal-result.json').read_text())
assert r['decision']=='PASS_CALLER_INTEGRATION'
assert r['caller_git_blob']=='7faf042304728ce91a3e4f89d465b251ea0bf70d'
assert r['source_quiet_result_git_blob']=='0627dba669903d3d8cc6e707cae9b9d329a623e5'
assert r['valid_cases']==3 and r['valid_execution_incomplete']==3
assert r['privacy_controls']==3 and r['privacy_control_execution_incomplete']==3
assert r['fault_cases']==27 and r['faults_failed_closed']==27 and r['faults_task_succeeded']==0
assert r['verify_effect_calls']==0 and not r['hard_failures']
print('PASS compact authority-ended adaptive caller integration audit')
