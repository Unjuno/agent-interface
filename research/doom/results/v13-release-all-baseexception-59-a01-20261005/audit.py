import json
from pathlib import Path
p=Path(__file__).parent
baseline=json.loads((p/'raw-baseline.json').read_text(encoding='utf-8'))
candidate=json.loads((p/'raw-candidate.json').read_text(encoding='utf-8'))
expected={'schema':'release-batch-delivery-v1','identifier':'cleanup','step':0,'size':1,'positions':[{'position':0,'step':0,'key':'a','state':'unknown'}]}
assert baseline['escaped']=='KeyboardInterrupt: cleanup sink interruption'
assert baseline['terminal_count']==0 and baseline['terminal'] is None
assert candidate['escaped']=='KeyboardInterrupt: cleanup sink interruption'
assert candidate['terminal_count']==1
terminal=candidate['terminal']
assert terminal['status']=='failed'
assert terminal['release']['verified'] is False
assert terminal['release']['error']=='KeyboardInterrupt(\'cleanup sink interruption\')'
assert terminal['release']['release_batch_delivery']==expected
print(json.dumps({'audit':'PASS','baseline_terminal_count':baseline['terminal_count'],'candidate_status':terminal['status'],'candidate_terminal_count':candidate['terminal_count'],'custody_match':True,'interrupt_preserved':True},sort_keys=True))

