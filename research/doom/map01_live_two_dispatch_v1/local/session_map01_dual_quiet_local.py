"""Local path adapter: MAP01 v13 with dual-lifetime executor + exact quiet hold backend."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=Path('/mnt/data/runtime-preview-extracted')
DOOM=ROOT/'research/doom';LIVE=ROOT/'research/live_control'
sys.path[:0]=[str(HERE),str(LIVE),str(DOOM)]
import doom_retained_input_backend_v3 as retained
from quiet_hold_backend_v1 import Backend as QuietBackend
retained.Backend = QuietBackend
import session_map01_v12 as base
from dual_lifetime_executor_v1 import Executor
base.Executor = Executor
import session_map01_v13 as v13
if __name__=='__main__':v13.main()
