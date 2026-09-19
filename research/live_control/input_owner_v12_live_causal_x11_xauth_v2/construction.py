from pathlib import Path
import importlib.util,json,os,tempfile

HERE=Path(__file__).resolve().parent
RUNNER=HERE/'reconstructed_source'/'runner.py'
spec=importlib.util.spec_from_file_location('runner1261',RUNNER);runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

def main(repo_root,out):
    out=Path(out)
    if out.exists(): raise SystemExit('construction result exists')
    out.parent.mkdir(parents=True,exist_ok=True)
    case_root=out.parent/'construction_cases';case_root.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='ai1261-xauth-') as xa, tempfile.TemporaryDirectory(prefix='ai1261-deps-') as td:
        auth=Path(xa)/'Xauthority';auth.write_bytes(b'');os.chmod(auth,0o600)
        old=os.environ.get('XAUTHORITY');os.environ['XAUTHORITY']=str(auth)
        try:
            deps=runner.source_gate(repo_root,td)
            rows=[runner.session(case_root,deps,'V10_BASELINE',0,'construction_1',1600),runner.session(case_root,deps,'V12_MEASURED',0,'construction_2',1601)]
        finally:
            if old is None: os.environ.pop('XAUTHORITY',None)
            else: os.environ['XAUTHORITY']=old
    result={'task':runner.TASK,'phase':'excluded_construction','construction_sessions':2,'formal_invocations':0,'reruns':0,'rows':rows,'summary':runner.summarize(rows),'xauthority_mode':'fresh_empty_file_with_xvfb_ac'}
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result['summary'],sort_keys=True))

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--repo-root',required=True);ap.add_argument('--out',required=True);a=ap.parse_args();main(a.repo_root,a.out)
