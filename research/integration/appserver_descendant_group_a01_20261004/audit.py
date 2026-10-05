import hashlib,json,pathlib,sys
r=pathlib.Path(__file__).resolve().parent
plan=(r/'PLAN.md').read_bytes(); source=(r/'codex_app_server_client_v2.py').read_bytes()
data=json.loads((r/'RESULT.json').read_text(encoding='utf-8'))
assert data['source_sha256']==hashlib.sha256(source).hexdigest()
assert data['main_sha']=='4d42238694c55aaa29bf47cb13a5b8d4c5d4074a'
a,b=data['arms']; assert len(data['arms'])==2
assert a['close_error'] and a['after_close']['reader_alive'] and a['after_close']['grandchild'] is not None
assert a['final_grandchild'] is None or a['final_grandchild']['state']=='Z'
assert a['final_reader_alive'] is False
assert b['close_error'] is None and not b['after_close']['reader_alive']
assert b['after_close']['grandchild'] is None or b['after_close']['grandchild']['state']=='Z'
assert b['after_close']['direct_rc'] is not None
print(json.dumps({'audit':'PASS_MECHANISM_COMPARISON','plan_bytes':len(plan),'plan_sha256':hashlib.sha256(plan).hexdigest(),'source_bytes':len(source),'source_sha256':hashlib.sha256(source).hexdigest(),'baseline_close_error':a['close_error'],'baseline_reader_after_close':a['after_close']['reader_alive'],'baseline_grandchild_alive_after_close':a['after_close']['grandchild'] is not None and a['after_close']['grandchild']['state']!='Z','group_close_error':b['close_error'],'group_reader_after_close':b['after_close']['reader_alive'],'group_grandchild_dead_or_reaped':b['after_close']['grandchild'] is None or b['after_close']['grandchild']['state']=='Z'},sort_keys=True))
