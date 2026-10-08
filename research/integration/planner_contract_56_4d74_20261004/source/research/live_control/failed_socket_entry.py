"""Test-only failed evaluator subprocess inside frozen socket v10."""
import sys
from pathlib import Path
import event_socket_v10 as bridge
marker=sys.argv.pop(1);original=bridge.subprocess.Popen
def spawn(args,**kwargs):
    args=list(args);index=next(i for i,a in enumerate(args) if str(a).endswith('interactive_v26.py'))
    args[index:index+1]=[str(Path(__file__).with_name('failed_evaluation_entry.py')),marker]
    return original(args,**kwargs)
bridge.subprocess.Popen=spawn
bridge.main()
