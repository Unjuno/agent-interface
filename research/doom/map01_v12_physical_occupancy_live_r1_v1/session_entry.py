"""Launch exact MAP01 v13 while substituting only the measurement owner implementation."""
import hashlib,json,os,sys
from pathlib import Path
source=Path(os.environ['MAP01_SOURCE_ROOT']).resolve(); v12=Path(os.environ['MAP01_V12_ROOT']).resolve(); exp=Path(__file__).resolve().parent
for p in (source/'research/live_control',source/'research/observation_gating',source/'research/doom',v12,exp):
    sys.path.insert(0,str(p))
# The repository has historical same-name modules in doom/ and live_control/.
# Make the shared live-control lineage authoritative before importing the v3 backend:
# live_control/session_v8 -> live_control/session_v7 -> live_control/session_v6.
sys.path.insert(0,str(source/'research/live_control'))
import doom_retained_input_backend_v3 as backend
from map01_v12_transition_owner import InputOwner
backend.InputOwner=InputOwner
import session_map01_v13

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
try:
    session_map01_v13.main()
finally:
    args=sys.argv[1:]
    if '--out' in args:
        out=Path(args[args.index('--out')+1]); sp=out/'sources.json'
        if sp.exists():
            data=json.loads(sp.read_text())
            data['external/map01_v12_transition_owner.py']=sha(exp/'map01_v12_transition_owner.py')
            data['external/input_owner_v12.py']=sha(v12/'input_owner_v12.py')
            data['external/adapter_contract.py']=sha(v12/'adapter_contract.py')
            sp.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
