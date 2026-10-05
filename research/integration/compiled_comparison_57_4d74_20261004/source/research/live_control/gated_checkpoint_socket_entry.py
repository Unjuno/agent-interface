"""Socket v14 with a test-gated artifact verifier."""
import sys
from pathlib import Path
import event_socket_v14 as bridge
gate=sys.argv.pop(1);original=bridge.subprocess.Popen
def spawn(args,**kwargs):
    args=list(args);index=next(i for i,a in enumerate(args) if str(a).endswith('interactive_v29.py'))
    args[index:index+1]=[str(Path(__file__).with_name('gated_checkpoint_entry.py')),gate]
    return original(args,**kwargs)
bridge.subprocess.Popen=spawn
bridge.main()
