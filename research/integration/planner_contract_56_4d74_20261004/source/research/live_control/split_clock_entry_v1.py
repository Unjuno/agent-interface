"""Use unchanged private socket bridge with synthetic split-clock subprocess."""
from pathlib import Path
import stopped_socket_v1 as bridge
original=bridge.subprocess.Popen
def spawn(args,**kwargs):
 args=list(args);i=next(i for i,a in enumerate(args) if str(a).endswith('interactive_v27.py'));args[i]=str(Path(__file__).with_name('split_clock_fixture_v1.py'));return original(args,**kwargs)
bridge.subprocess.Popen=spawn
if __name__=='__main__':bridge.main()
