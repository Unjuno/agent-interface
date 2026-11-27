import hashlib, json, os, platform, re, subprocess, sys, time
from pathlib import Path
root=Path(os.environ.get('A07_INPUTS','/inputs')).resolve(); output=Path(os.environ.get('A07_RESULTS','/results'))
limits={}
for name,path in [('cpu.max','/sys/fs/cgroup/cpu.max'),('memory.max','/sys/fs/cgroup/memory.max')]:
    try: limits[name]=Path(path).read_text().strip()
    except OSError as e: limits[name]=f'UNAVAILABLE:{type(e).__name__}'
cases=[]
for impl in ('main','candidate'):
    source=(root/impl).resolve(); tests=(root/'tests').resolve()
    for opt in (False,True):
        bootstrap=(
            'import hashlib,importlib,pathlib,sys,unittest; '
            f'm=importlib.import_module("doom_controller_failure_cleanup_v1"); '
            f'p=pathlib.Path(m.__file__).resolve(); expected=pathlib.Path({str(source / "doom_controller_failure_cleanup_v1.py")!r}).resolve(); '
            'print("SOURCE_PATH="+str(p)); print("SOURCE_SHA256="+hashlib.sha256(p.read_bytes()).hexdigest()); '
            'assert p==expected, f"source path mismatch: {p} != {expected}"; '
            f'sys.path.insert(0,{str(tests)!r}); '
            'suite=unittest.defaultTestLoader.loadTestsFromName("test_controller_failure_cleanup_v39"); '
            'result=unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(not result.wasSuccessful())'
        )
        cmd=[sys.executable]+(['-O'] if opt else [])+['-c',bootstrap]
        env=os.environ.copy(); env['PYTHONPATH']=str(source); env['PYTHONDONTWRITEBYTECODE']='1'
        started=time.perf_counter()
        p=subprocess.run(cmd,cwd=tests,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        out=p.stdout
        fails=re.findall(r'^FAIL: ([^(]+)',out,re.M); errors=re.findall(r'^ERROR: ([^(]+)',out,re.M)
        count=re.search(r'Ran (\d+) tests?',out)
        source_path=re.search(r'^SOURCE_PATH=(.+)$',out,re.M); source_sha=re.search(r'^SOURCE_SHA256=([0-9a-f]+)$',out,re.M)
        cases.append({'implementation':impl,'optimized':opt,'command':cmd,'exit_code':p.returncode,'test_count':int(count.group(1)) if count else None,'failed_tests':fails,'errored_tests':errors,'source_path':source_path.group(1) if source_path else None,'source_sha256':source_sha.group(1) if source_sha else None,'expected_source_path':str(source/'doom_controller_failure_cleanup_v1.py'),'source_path_match':bool(source_path and Path(source_path.group(1)).resolve()==(source/'doom_controller_failure_cleanup_v1.py').resolve()),'elapsed_seconds':round(time.perf_counter()-started,4),'raw_output':out})
expected={'test_duplicate_acceptance_identity_is_ambiguous','test_conflicting_duplicate_terminals_are_order_independent'}
valid=True
for c in cases:
    got=set(c['failed_tests'])|set(c['errored_tests'])
    valid &= c['source_path_match'] and c['test_count']==5
    if c['implementation']=='candidate': valid &= c['exit_code']==0 and not got
    else: valid &= c['exit_code']!=0 and got==expected and not c['errored_tests']
result={'status':'PASS_SCOPED' if valid else 'FAIL_SCOPED','python':platform.python_version(),'platform':platform.platform(),'requested_container_constraints':{'cpus':'1','memory':'512m','network':'none'},'observed_local_cgroup':limits,'runtime':'native Ubuntu WSL (WSLc file bind mount did not expose /runner; see attempts.jsonl)','cases':cases}
output.mkdir(parents=True,exist_ok=True); (output/'run.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='cases'},sort_keys=True))
for c in cases: print(json.dumps({k:c[k] for k in ('implementation','optimized','exit_code','test_count','failed_tests','errored_tests','source_path_match','elapsed_seconds')},sort_keys=True))
sys.exit(0 if valid else 1)

