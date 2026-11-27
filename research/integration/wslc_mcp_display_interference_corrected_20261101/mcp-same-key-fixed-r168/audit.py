import hashlib,json,pathlib
r=pathlib.Path(__file__).resolve().parent;p=r/'r168-same';m=json.loads((r/'manifest.json').read_text());c=json.loads((p/'conditions.json').read_text());d=json.loads((p/'output/result.json').read_text());l=json.loads((p/'launcher-result.json').read_text());prev=json.loads((r.parent/'idle-two-mcp-same-key-r150'/'manifest.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
assert all(sha((r/k).read_bytes())==v for k,v in m.items()) and c['manifest_sha256']==sha((r/'manifest.json').read_bytes());a={k:v for k,v in m.items() if k.startswith('src/')};b={k:v for k,v in prev.items() if k.startswith('src/')};assert set(a)==set(b) and [k for k in a if a[k]!=b[k]]==['src/runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py']
assert l['returncode']==0 and d['status']=='passed' and d['before_second']['a'] and not d['after_fixture_release']['a'] and d['second_hold_before_cancel']['a'] and not d['second_hold_after_first_cancel']['a'] and all(len(v)==1 for v in d['injections'].values())
for key in ('first_terminal','second_terminal'):
 x=d[key];assert x['status']=='runtime_failed' and x['cleanup_status']=='UNKNOWN' and x['cancellation']['status']=='completed' and x['cancellation']['result']['owner_release_attempt']['status']=='readback_verified' and not x['cancellation']['replay_allowed']
for key in ('first_close_final','second_close_final'):assert d[key]['status']=='cleanup_failed' and d[key]['cleanup_status']=='UNKNOWN'
assert [(e['type'],e['key']) for e in d['target_result']['events']]==[('press','a'),('release','a'),('press','a'),('release','a')] and d['horizon']=={'a':False,'b':False,'c':False} and d['target_exit']==d['server_exit']==0
print('PASS: one injection each; old MCP cleanup interferes with second same-key hold')
