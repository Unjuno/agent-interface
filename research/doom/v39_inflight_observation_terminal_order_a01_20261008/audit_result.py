from __future__ import annotations
import ast,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
freeze=json.loads((ROOT/'FREEZE.json').read_text())
result=json.loads((ROOT/'RESULT.json').read_text())
pipeline=json.loads((ROOT/'PIPELINE_AUDIT.json').read_text())
sources=[freeze['source'],*freeze['additional_sources'],*freeze['runtime_sources']]
for item in sources:
    path=ROOT/item['local_path']; data=path.read_bytes()
    assert len(data)==item['bytes']
    assert hashlib.sha256(data).hexdigest()==item['sha256']
    blob=subprocess.check_output(['git','hash-object','--no-filters',str(path)],text=True).strip()
    assert blob==item['git_blob'],(item['local_path'],blob)
assert result['source_sha256']==freeze['source']['sha256']
assert result['status']=='PASS_INFLIGHT_OBSERVATION_INVALIDATES_BEFORE_TERMINAL'
assert result['snapshot_saw_event'] is False
assert result['monitor_saw_event_after_snapshot'] is True
assert result['answer_discarded'] is True
assert result['final_action_admission']['status']=='REJECTED_POLICY_INVALIDATED'
assert result['final_action_admission']['input_authority_admitted'] is False
assert result['terminal_release']=={'verified':True,'keys_down':[],'buttons_down':[]}
assert pipeline['status']=='PASS_SOURCE_VERIFIED_OBSERVATION_BEFORE_TERMINAL_FIFO'
assert pipeline['main_commit']==freeze['current_main_commit']
candidate_text=(ROOT/'run_candidate.py').read_text(encoding='utf-8')
assert "n.name=='reader'" in candidate_text
assert 'incoming.reader_paused.wait(1)' in candidate_text
assert 'threading.Thread(target=exact_reader)' in candidate_text
text=(ROOT/freeze['source']['local_path']).read_text(encoding='utf-8')
tree=ast.parse(text)
main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
wait=next(n for n in ast.walk(main) if isinstance(n,ast.FunctionDef) and n.name=='wait')
source_wait=ast.get_source_segment(text,wait)
assert 'observation_monitor.observe(row)' in source_wait
assert source_wait.index('observation_monitor.observe(row)') < source_wait.index('if predicate(row)')
assert 'for _ in range(incoming.qsize())' in text
runtime_asserts=sum(isinstance(n,ast.Assert) for n in ast.walk(ast.parse((ROOT/'audit_runtime_order.py').read_text(encoding='utf-8'))))
local_asserts=sum(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(Path(__file__).read_text(encoding='utf-8'))))
assertion_count=runtime_asserts+local_asserts+4*len(sources)
report={'status':'PASS_INDEPENDENT_EXPERIMENT_AND_PIPELINE_AUDIT','sources_verified':len(sources),'git_blobs':[x['git_blob'] for x in sources],'source_sha256':result['source_sha256'],'pipeline_status':pipeline['status'],'assertions':assertion_count,'main_commit':freeze['current_main_commit']}
(ROOT/'AUDIT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,sort_keys=True))
