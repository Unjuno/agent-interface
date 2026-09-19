"""Private socket test entry for actual target mutation; ordinary runtime unchanged."""
from pathlib import Path
import os,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'live_control'))
import stopped_socket_v1 as bridge
kind=sys.argv.pop(1)
if kind not in ('patch','focus'):raise ValueError(kind)
os.environ['AI_STUDY_MUTATION']=kind
original=bridge.subprocess.Popen
def spawn(args,**kwargs):
 args=list(args);i=next(i for i,a in enumerate(args) if str(a).endswith('interactive_v27.py'));args[i]=str(HERE/'mindustry_menu_mutation_fixture_v2.py');return original(args,**kwargs)
bridge.subprocess.Popen=spawn
if __name__=='__main__':bridge.main()
