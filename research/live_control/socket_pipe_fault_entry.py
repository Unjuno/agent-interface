"""Test-only substitution of paused stdin runtime and a 4096-byte pipe."""
import fcntl,sys
from pathlib import Path
import event_socket_v6 as bridge
marker=sys.argv.pop(1);original=bridge.subprocess.Popen
def spawn(args,**kwargs):
    args=list(args);i=next(i for i,a in enumerate(args) if str(a).endswith('interactive_v23.py'))
    args[i:i+1]=[str(Path(__file__).with_name('stdin_pause_entry.py')),marker]
    p=original(args,**kwargs);fcntl.fcntl(p.stdin.fileno(),fcntl.F_SETPIPE_SZ,4096);return p
bridge.subprocess.Popen=spawn
bridge.main()
