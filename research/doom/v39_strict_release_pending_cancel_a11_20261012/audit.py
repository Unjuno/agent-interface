import hashlib,json,pathlib,subprocess,sys
p=pathlib.Path(__file__).parent
m=json.loads((p/'SOURCE_MANIFEST.json').read_text())
checks=[]
def check(name,ok,detail=''):
 checks.append({'name':name,'ok':bool(ok),'detail':detail})
for rel,meta in m['files'].items():
 data=(p/rel).read_bytes()
 check('sha256:'+rel,hashlib.sha256(data).hexdigest()==meta['sha256'] and len(data)==meta['bytes'],f"bytes={len(data)}")
for key,rel in [('main','sources/main_controller.py'),('strict_pr8835','sources/strict_controller.py'),('a10_guard','sources/observable_signal_guard_v2.py'),('a10_adapter','sources/persistent_planner_adapter_v2.py'),('a10_test','sources/a10_test_original.py')]:
 data=(p/rel).read_bytes(); blob=hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
 check('git_blob:'+key,blob==m['git_blobs'][key],blob)
t=(p/'test_strict_release_pending_cancel_integration.py').read_text()
for s in ['"verified": True, "keys_down": [], "buttons_down": [],\n             "key_state_errors": []','"keys_unknown": ["KEY_W"]','"keys_unknown": []','"key_state_errors": [{"source": "keymap_after"}]']:
 check('mutation:'+str(len(checks)),s in t)
for mode in ['normal','optimized']:
 log=(p/'raw'/f'stdout-{mode}.txt').read_text(); code=(p/f'raw-{mode}.exit').read_text(encoding='utf-8-sig').replace('exit=','').strip()
 check('run:'+mode,code=='0' and 'Ran 2 tests' in log and 'OK' in log and 'FAILED' not in log, f'exit={code}')
 result=next((line.split('A11_COMPOSED_RESULT=',1)[1] for line in log.splitlines() if 'A11_COMPOSED_RESULT=' in line),None)
 try: r=json.loads(result) if result else {}
 except Exception: r={}
 check('result:'+mode,r.get('timeline')==['executor_cancel_write','executor_flush','planner_interrupt_request','planner_interrupt_ack'] and r.get('planner_result',{}).get('answer_eligible') is False and r.get('planner_result',{}).get('answer') is None and r.get('terminal_release',{}).get('keys_unknown')==[] and r.get('terminal_release',{}).get('key_state_errors')==[],json.dumps(r,sort_keys=True))
 check('swap_limitation_recorded:'+mode,'swap' in json.loads((p/'RUN.json').read_text(encoding='utf-8-sig'))['swap_warning'])
img=json.loads((p/'raw/image-inspect.json').read_text())[0]
check('image',img['Id']=='sha256:16cfda0e6a1d9077709d0cbcd378562b025bb82d8243de633da2ab31d6489cb7' and 'python@sha256:b9767f56a1cc620aa72d38cc3557d26412e38a4597c92953476136b78894ccbd' in img['RepoDigests'])
check('containers-empty','\n' not in (p/'raw/container-inventory-after.txt').read_bytes().decode('utf-8',errors='replace').strip() or len((p/'raw/container-inventory-after.txt').read_bytes().splitlines())<=2)
out={'audit':'PASS' if all(c['ok'] for c in checks) else 'FAIL','passed':sum(c['ok'] for c in checks),'total':len(checks),'checks':checks}
(p/'AUDIT.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k] for k in ['audit','passed','total']}))
for c in checks:
 if not c['ok']: print('FAIL',c['name'],c['detail'])
sys.exit(0 if out['audit']=='PASS' else 1)

