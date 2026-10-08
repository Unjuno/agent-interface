from __future__ import annotations
import ast,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
freeze=json.loads((ROOT/'FREEZE.json').read_text())
source=(ROOT/freeze['source']['local_path']).read_bytes()
result=json.loads((ROOT/'RESULT.json').read_text())
assert hashlib.sha256(source).hexdigest()==freeze['source']['sha256']
blob=subprocess.check_output(['git','hash-object',str(ROOT/freeze['source']['local_path'])],text=True).strip()
assert blob==freeze['source']['git_blob']
assert result['source_sha256']==freeze['source']['sha256']
assert result['status']=='PASS_INFLIGHT_OBSERVATION_INVALIDATES_BEFORE_TERMINAL'
assert result['snapshot_saw_event'] is False
assert result['monitor_saw_event_after_snapshot'] is True
assert result['answer_discarded'] is True
assert result['events'].index('bounded_snapshot_empty') < result['events'].index('wait_returns_policy_invalidation') < result['events'].index('matching_cover_terminal') < result['events'].index('completed_answer_discarded')
assert result['terminal_release']=={'verified':True,'keys_down':[],'buttons_down':[]}
tree=ast.parse(source.decode('utf-8'))
main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
wait=next(n for n in ast.walk(main) if isinstance(n,ast.FunctionDef) and n.name=='wait')
source_wait=ast.get_source_segment(source.decode('utf-8'),wait)
assert 'observation_monitor.observe(row)' in source_wait
assert source_wait.index('observation_monitor.observe(row)') < source_wait.index('if predicate(row)')
assert 'for _ in range(incoming.qsize())' in source.decode('utf-8')
report={'status':'PASS_INDEPENDENT_SOURCE_EVENT_AUDIT','git_blob':blob,'source_sha256':result['source_sha256'],'assertions':13,'main_commit':freeze['current_main_commit']}
(ROOT/'AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,sort_keys=True))
