import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;LIVE=Path('/tmp/lab/src/research/live_control');DOOM=Path('/tmp/lab/src/research/doom')
sys.path[:0]=[str(HERE),str(LIVE),str(DOOM)]
import doom_retained_input_backend_v3 as retained
from guard_band_hold_backend_v1 import Backend as GuardBackend
retained.Backend=GuardBackend
import session_map01_v12 as base
from dual_lifetime_executor_v1 import Executor
base.Executor=Executor
import session_map01_v13 as v13
if __name__=='__main__':v13.main()
