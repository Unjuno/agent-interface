import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3]
PKG=pathlib.Path(__file__).resolve().parent
freeze=json.loads((PKG/'FREEZE.json').read_text(encoding='utf-8'))
runs=json.loads((PKG/'RUN_RECORD.json').read_text(encoding='utf-8'))
checks=[]
def check(name,ok): checks.append({'name':name,'passed':bool(ok)})
check('base commit matches run record',freeze['base_commit']==runs['base_commit'])
check('working source hashes',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in freeze['worktree_source_sha256'].items()))
check('test hash',hashlib.sha256((PKG/'test_stale_rejection_recovery.py').read_bytes()).hexdigest()==freeze['test_sha256'])
check('normal regression pass',runs['runs']['normal']['passed'] and runs['runs']['normal']['test_count']==63)
check('optimized regression pass',runs['runs']['optimized']['passed'] and runs['runs']['optimized']['test_count']==63)
check('normal retained log',('\nRan 63 tests' in (PKG/'normal-tests.txt').read_text() and (PKG/'normal-tests.txt').read_text().rstrip().endswith('OK')))
check('optimized retained log',('\nRan 63 tests' in (PKG/'optimized-tests.txt').read_text() and (PKG/'optimized-tests.txt').read_text().rstrip().endswith('OK')))
check('no formal allocation',freeze['formal_allocation_invocations']==0)
check('no live input',freeze['live_app_or_os_input'] is False)
report={'schema':'v39-stale-ack-recovery-audit-v1','checks_passed':sum(c['passed'] for c in checks),'checks_total':len(checks),'passed':all(c['passed'] for c in checks),'checks':checks}
(PKG/'AUDIT.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(f"{report['checks_passed']}/{report['checks_total']}")
if not report['passed']: raise SystemExit(1)
