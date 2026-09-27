from pathlib import Path
import sys
ROOT=Path('/mnt/data/release_real_setup/src')
sys.path.insert(0,str(ROOT/'research/doom'))
sys.path.insert(0,str(ROOT/'research/live_control'))
sys.path.insert(0,str(ROOT/'research/observation_gating'))
import doom_retained_input_backend_v3 as retained
from two_phase_map01_candidate_backend import Backend
retained.Backend=Backend
import session_map01_v13
if __name__=='__main__': session_map01_v13.main()
