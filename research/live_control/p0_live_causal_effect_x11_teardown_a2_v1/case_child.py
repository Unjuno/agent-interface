from __future__ import annotations
import argparse,importlib.util,json,subprocess,sys,tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
SCIENCE=HERE/'science_runner.py'

def load_science():
    name='science_runner_1301'
    spec=importlib.util.spec_from_file_location(name,SCIENCE)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

class ExternalXvfbHandle:
    def poll(self): return 0
    def terminate(self): return None
    def kill(self): return None
    def wait(self,timeout=None): return 0

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo-root',required=True);ap.add_argument('--case-root',required=True)
    ap.add_argument('--arm',required=True);ap.add_argument('--pair',type=int,required=True);ap.add_argument('--position',type=int,required=True)
    ap.add_argument('--display-num',type=int,required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    science=load_science(); original_popen=subprocess.Popen
    def routed_popen(args,*x,**kw):
        if isinstance(args,(list,tuple)) and args and Path(str(args[0])).name=='Xvfb':
            return ExternalXvfbHandle()
        return original_popen(args,*x,**kw)
    subprocess.Popen=routed_popen
    try:
        with tempfile.TemporaryDirectory(prefix='ai1301deps-') as td:
            deps=science.source_gate(a.repo_root,td)
            row=science.one_session(a.case_root,deps,a.arm,a.pair,a.position,a.display_num)
        Path(a.out).write_text(json.dumps(row,indent=2,sort_keys=True)+'\n')
    finally:
        subprocess.Popen=original_popen

if __name__=='__main__':main()
