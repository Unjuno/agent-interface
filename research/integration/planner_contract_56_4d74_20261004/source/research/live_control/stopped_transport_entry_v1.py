"""Use actual stopped socket transport with the controlled capture fixture."""
from pathlib import Path
import stopped_socket_v1 as bridge
original=bridge.subprocess.Popen
def spawn(args,**kwargs):
    args=list(args)
    index=next(i for i,a in enumerate(args) if str(a).endswith('interactive_v27.py'))
    args[index]=str(Path(__file__).with_name('stopped_transport_fixture_v1.py'))
    return original(args,**kwargs)
bridge.subprocess.Popen=spawn
bridge.main()
