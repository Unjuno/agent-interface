def main():
    import hashlib,json,os,platform,subprocess,sys,time
    from pathlib import Path
    ROOT=Path(__file__).resolve().parent.parents[2]
    OUT=Path(sys.argv[1]).resolve();OUT.mkdir(parents=True,exist_ok=False)
    PY=sys.executable
    module='research.doom.test_map01_overlap_controller_v39.Map01V39CoastTests.'
    targets=[module+name for name in ['test_pending_health_invalidation_interrupts_before_completion','test_pending_unknown_health_interrupts_before_completion','test_pending_invalidation_does_not_replan_without_neutral_release']]
    if len(sys.argv)>2 and sys.argv[2]=='focused':
     targets=['research.doom.test_map01_overlap_controller_v39','research.live_control.test_observable_signal_guard_v2']
    cmd=[PY,'-B','-m','unittest','-v',*targets]
    m=json.loads((ROOT/'research/doom/invalidation_identity_59_e0cc_20261005/baseline-source-manifest.json').read_text())
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in m['files']}
    env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join(str(ROOT/p) for p in ['research/doom','research/live_control']);env['AI_PENDING_TEST_OUT']=str(OUT/'traces')
    (OUT/'pre-run.json').write_text(json.dumps({'command':cmd,'source_sha256':hashes,'classification':'ordinary deterministic controller regression; no formal allocation'},indent=2)+'\n')
    start=time.time_ns();r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,timeout=90);end=time.time_ns()
    (OUT/'stdout.txt').write_bytes(r.stdout);(OUT/'stderr.txt').write_bytes(r.stderr)
    receipt={'command':cmd,'cwd':str(ROOT),'PYTHONPATH':env['PYTHONPATH'],'trace_directory':env['AI_PENDING_TEST_OUT'],'started_unix_ns':start,'finished_unix_ns':end,'exit_code':r.returncode,'python':platform.python_version(),'platform':platform.platform(),'source_sha256':hashes,'sources_unchanged':all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items()),'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(r.stderr).hexdigest()}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'label':sys.argv[1],'exit_code':r.returncode,'sources_unchanged':receipt['sources_unchanged']}));print(r.stderr.decode()[-6000:])

    raise SystemExit(r.returncode)

if __name__ == "__main__":
    main()
