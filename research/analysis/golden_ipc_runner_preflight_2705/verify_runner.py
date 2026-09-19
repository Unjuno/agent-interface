"""Static preflight for #2705's container-host model IPC prerequisites."""
from __future__ import annotations
import json
from pathlib import Path

REQUIRED = (
    Path("container_host_model_ipc_runner_v1.py"),
    Path("host_model_ipc_broker_v1.py"),
)
def verify() -> dict:
    missing=[str(p).replace("\\","/") for p in REQUIRED if not p.is_file()]
    return {
        "schema":"golden-ipc-runner-preflight-2705-v1",
        "decision":"READY_FOR_ALLOCATION" if not missing else "HOLD_INFRASTRUCTURE",
        "missing_required_sources":missing,
        "model_calls":0,
        "gui_operations":0,
        "input_operations":0,
        "task_effect":0,
        "allocation_started":False,
    }
if __name__=="__main__":
    print(json.dumps(verify(),indent=2,sort_keys=True))
