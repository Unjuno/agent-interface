def main():
    import ast,hashlib,json,os,platform,subprocess,time,difflib,sys
    from pathlib import Path
    ROOT=Path(sys.argv[1]).resolve()
    REPO=ROOT
    OUT=Path(sys.argv[2]).resolve()
    OUT.mkdir(parents=True,exist_ok=False)
    PARENT='edcf29449d4f700fee8c87dc93f9aef7862bd5af'
    CARRIER='95666c514f142b58cebafc1920b86bcd87a0d8be'
    GIT='git'
    PYTHON=sys.executable
    OWNER='research/live_control/input_owner_v12.py'
    TEST='research/live_control/test_input_owner_v12_explicit_up_cancel.py'
    METHOD='test_lost_explicit_keyup_is_retried_and_receipt_uses_server_keymap'
    closure=json.loads((REPO/'research/live_control/results/wheel-successor-regression-e0cc-20261005/successor-source-manifest.json').read_text())['files']
    VIEW=OUT/'source'
    VIEW.mkdir(exist_ok=False)
    source={}
    for path in closure:
        b=subprocess.check_output([GIT,'show',PARENT+':'+path],cwd=REPO)
        dest=VIEW/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
        source[path]={'ref':PARENT,'sha256':hashlib.sha256(b).hexdigest()}
    base=(VIEW/TEST).read_text()
    carrier=(Path(__file__).resolve().parent/'carrier-test-original.py.txt').read_text()
    def bounds(t):
        node=next(x for x in ast.walk(ast.parse(t)) if isinstance(x,ast.FunctionDef) and x.name==METHOD)
        return node.lineno-1,node.end_lineno
    lo,hi=bounds(base);a,b=bounds(carrier)
    extracted=''.join(base.splitlines(keepends=True)[:lo]+carrier.splitlines(keepends=True)[a:b]+base.splitlines(keepends=True)[hi:])
    (OUT/'extracted-test.py.txt').write_text(extracted)
    patch=''.join(difflib.unified_diff(base.splitlines(True),extracted.splitlines(True),fromfile='a/'+TEST,tofile='b/'+TEST))
    (OUT/'extracted-cleanup.patch').write_text(patch)
    owner=(VIEW/OWNER).read_bytes()
    old=b'                attempts, verified = release_key(code)\n'
    assert owner.count(old)==1
    redundant=owner.replace(old,b'                attempts, verified = release_key(code, force_first=True)\n')
    point=b'            release_codes.extend(sorted(set(touched) - set(held)))\n'
    assert owner.count(point)==1
    skip=owner.replace(point,point+b'            if any(row.get("event") == "owner_explicit_keyup" and row.get("server_keyup_verified") is False for row in self.records):\n                release_codes = []\n')
    point2=b'            self.records.append(record)\n'
    assert owner.count(point2)==1
    purge=owner.replace(point2,b'            self.records[:] = [row for row in self.records if not (row.get("event") == "owner_explicit_keyup" and row.get("server_keyup_verified") is False)]\n'+point2)
    anchor='            self.assertFalse(failed_receipt["server_keyup_verified"])\n            self.assertEqual(len(cleanup_after_failure'
    assert extracted.count(anchor)==1
    strengthened=extracted.replace(anchor,'            self.assertIn(failed_receipt, owner.records)\n'+anchor)
    (OUT/'strengthened-test.py.txt').write_text(strengthened)
    (OUT/'recommended-cleanup.patch').write_text(''.join(difflib.unified_diff(base.splitlines(True),strengthened.splitlines(True),fromfile='a/'+TEST,tofile='b/'+TEST)))
    cases=[('baseline_extracted',owner,extracted,0),('redundant_terminal_up',redundant,extracted,1),('skip_failed_cleanup',skip,extracted,1),('erase_failed_receipt',purge,extracted,None),('baseline_strengthened',owner,strengthened,0),('erase_failed_receipt_strengthened',purge,strengthened,1)]
    freeze={'classification':'ordinary synthetic regression extraction and mutation controls; not formal allocation','parent':PARENT,'carrier':CARRIER,'method':METHOD,'H':'Existing cleanup assertions retain behavior on the release-pending successor and distinguish duplicate-UP, missing recovery and lost diagnostic regressions.','D':'Baseline must pass; mutation controls must fail to establish the asserted contract. A surviving mutation is a test-coverage finding, not a runtime defect.','limitations':'No real X, OS input, container, game, model, physical release or performance evidence.','source':source,'cases':[{'id':label,'owner_sha256':hashlib.sha256(ob).hexdigest(),'test_sha256':hashlib.sha256(tb.encode()).hexdigest(),'expected_exit':expect} for label,ob,tb,expect in cases]}
    (OUT/'freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
    results=[]
    for label,ob,tb,expect in cases:
        (VIEW/OWNER).write_bytes(ob);(VIEW/TEST).write_text(tb)
        cmd=[PYTHON,'-B','-m','unittest','test_input_owner_v12_explicit_up_cancel.ExplicitKeyUpCancellationTests.'+METHOD,'-v']
        env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join(str(VIEW/p) for p in ['research/live_control','research/doom'])
        start=time.time_ns();r=subprocess.run(cmd,cwd=VIEW,env=env,capture_output=True,timeout=60);end=time.time_ns()
        (OUT/(label+'.stdout.txt')).write_bytes(r.stdout);(OUT/(label+'.stderr.txt')).write_bytes(r.stderr)
        result={'case':label,'command':cmd,'cwd':str(VIEW),'PYTHONPATH':env['PYTHONPATH'],'started_unix_ns':start,'finished_unix_ns':end,'exit_code':r.returncode,'expected_exit':expect,'platform':platform.platform(),'owner_sha256':hashlib.sha256(ob).hexdigest(),'test_sha256':hashlib.sha256(tb.encode()).hexdigest(),'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest(),'owner_unchanged':(VIEW/OWNER).read_bytes()==ob,'test_unchanged':(VIEW/TEST).read_text()==tb}
        (OUT/(label+'.execution.json')).write_text(json.dumps(result,indent=2)+'\n');results.append(result)
        print(json.dumps({'case':label,'exit':r.returncode,'expected':expect}),flush=True)
        print(r.stderr.decode()[-1100:],flush=True)
    (VIEW/OWNER).write_bytes(owner);(VIEW/TEST).write_text(strengthened)
    (OUT/'results.json').write_text(json.dumps(results,indent=2)+'\n')

if __name__ == "__main__":
    main()
