import hashlib,json,os,re,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent; I=P/'inputs'; R=P/'results'
repo=os.environ.get('A07_GIT_REPO','/mnt/d/codex-research/issue59-stale-replan-pr-20261008')
freeze=json.loads((P/'FREEZE.json').read_text(encoding='utf-8'))
run=json.loads((R/'run.json').read_text(encoding='utf-8'))
expected_git={'main/controller.py':'50c63fa83969ed518a91e39c08d1ee52064eb636','candidate/controller.py':'576d481a3503e8be4d8ceded8a6371b3fe8850fc','candidate/test_controller_failure_cleanup_v39.py':'0bad8e47bb1a78798ad982fbd6be63c09d834742'}
expected_tests={'test_duplicate_acceptance_identity_is_ambiguous','test_conflicting_duplicate_terminals_are_order_independent'}
verified={}; errors=[]
paths={'main/controller.py':'research/doom/doom_controller_failure_cleanup_v1.py','candidate/controller.py':'research/doom/doom_controller_failure_cleanup_v1.py','candidate/test_controller_failure_cleanup_v39.py':'research/doom/test_controller_failure_cleanup_v39.py'}
for rel,path in paths.items():
    local=I/rel
    if not local.is_file(): errors.append(f'missing {rel}'); continue
    oid=subprocess.check_output(['git','-c','core.autocrlf=true','-C',repo,'hash-object',f'--path={path}',str(local)],text=True).strip()
    verified[rel]=oid
    if oid!=expected_git[rel]: errors.append(f'git blob mismatch {rel}: {oid}')
    meta=freeze.get('blobs',freeze).get(rel)
    if meta is None or meta.get('blob')!=oid: errors.append(f'freeze mismatch {rel}')
# Candidate test copy used for import must byte-match the frozen candidate test blob.
if hashlib.sha256((I/'tests/test_controller_failure_cleanup_v39.py').read_bytes()).digest()!=hashlib.sha256((I/'candidate/test_controller_failure_cleanup_v39.py').read_bytes()).digest(): errors.append('test copy differs from frozen source')
for c in run['cases']:
    impl=c['implementation']; mode='optimized' if c['optimized'] else 'normal'; out=c['raw_output']
    source_rel=f'{impl}/controller.py'; source=I/impl/'doom_controller_failure_cleanup_v1.py'
    if not c.get('source_path_match'): errors.append(f'{impl}/{mode}: imported source path mismatch')
    if c.get('source_sha256')!=hashlib.sha256(source.read_bytes()).hexdigest(): errors.append(f'{impl}/{mode}: imported source SHA-256 mismatch')
    if c.get('test_count')!=5: errors.append(f'{impl}/{mode}: wrong test count')
    fail_lines=re.findall(r'^FAIL: ([^(\r\n]+)',out,re.M)
    failures={x.strip() for x in fail_lines}
    error_lines=re.findall(r'^ERROR: ([^(\r\n]+)',out,re.M)
    if impl=='candidate':
        if c['exit_code']!=0 or failures or error_lines or 'OK' not in out: errors.append(f'candidate/{mode}: expected clean pass')
    else:
        if c['exit_code']==0 or failures!=expected_tests or len(fail_lines)!=3 or error_lines or 'FAILED (failures=3)' not in out: errors.append(f'main/{mode}: expected three assertions across exactly two duplicate-ID tests; got {fail_lines}')
result={'status':'PASS_SCOPED_WITH_ENVIRONMENT_DEVIATION' if not errors else 'FAIL_AUDIT','basis':'independent raw-output classification; runner summary status is retained as originally emitted','verified_git_blobs':verified,'main_expected_failed_test_names':sorted(expected_tests),'main_failed_assertions_per_mode':3,'candidate_tests_per_mode':5,'candidate_failures':0,'modes':['normal','optimized (-O)'],'environment_deviation':'WSLc attempts never exposed /runner from the D: bind mount and exited before suite execution; actual focused tests ran under native Ubuntu WSL CPython 3.12.3. No CPU/memory container limits are claimed.','raw_runner_classifier_issue':'The runner emitted FAIL_SCOPED because it compared test names with trailing whitespace and did not deduplicate unittest subtest failures. Raw output shows the intended two main test methods fail and all candidate tests pass.','errors':errors}
(R/'audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(result,sort_keys=True))
sys.exit(0 if not errors else 1)



