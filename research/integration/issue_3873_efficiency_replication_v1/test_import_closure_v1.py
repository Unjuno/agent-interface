"""Import the exact formal driver and GUI runtime in OrbStack without calls."""
from pathlib import Path
import os
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
LIVE=ROOT/"research/live_control"
sys.path[:0]=[str(LIVE),str(ROOT),str(ROOT/"runtime"),str(HERE)]
os.environ.setdefault("ISSUE3824_OUT","/tmp/issue-3873-import-only")
os.environ.setdefault("ISSUE3824_RUNNER",str(HERE/"container_host_model_ipc_runner_v3.py"))
os.environ.setdefault("ISSUE3824_MODEL_IMAGE","sha256:5cc4d237e6af4548147ddfffc35413faf2487fd585f6a0216221f153f61cf073")
os.environ.setdefault("ISSUE3824_RUNNER_IMAGE",os.environ["ISSUE3824_MODEL_IMAGE"])
os.environ.setdefault("ISSUE3824_CODEX_EXE","/opt/homebrew/bin/codex")
os.environ.setdefault("ISSUE3824_LIVE_SOURCE",str(LIVE))
import integrated_efficiency_client_v1
import integrated_efficiency_protocol_v1
import run_integrated_efficiency_live_v1
import issue3824_model_backend_v1
import issue3864_model_backend_v1
import event_socket_v11
print("PASS_FORMAL_IMPORT_CLOSURE_NO_MODEL_CALLS")
