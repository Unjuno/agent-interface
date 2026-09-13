"""Mindustry candidate behind unchanged private stopped-event socket transport."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'live_control'))
import stopped_socket_v1 as bridge
entry=HERE/'mindustry_bend_interactive_v2.py'
if sys.argv[1:2]==['--focus-fixture']:
 sys.argv.pop(1);entry=HERE/'mindustry_focus_fixture_v2.py'
original=bridge.subprocess.Popen
def spawn(args,**kwargs):
 args=list(args);index=next(i for i,a in enumerate(args) if str(a).endswith('interactive_v27.py'));args[index]=str(entry)
 return original(args,**kwargs)
bridge.subprocess.Popen=spawn
if __name__=='__main__':bridge.main()
