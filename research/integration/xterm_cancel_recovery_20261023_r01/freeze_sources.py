"""Explicit setup command that freezes the live trial's source identity."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NAMES = [
    str(Path(__file__).relative_to(ROOT)),
    str((HERE/'trial.py').relative_to(ROOT)),
    str((HERE/'record_helper.py').relative_to(ROOT)),
    str((HERE/'audit.py').relative_to(ROOT)),
    str((HERE/'native_preflight.py').relative_to(ROOT)),
    'runtime/backends/x11_v1/backend.py',
    'runtime/cli_v1/mcp_server.py',
    'runtime/cli_v1/mcp_guarded.py',
    'runtime/cli_v1/owned_guarded_session.py',
    'runtime/guarded_x11_v1/cancel_supervisor.py',
    'runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py',
]
rows = {name:hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
        for name in NAMES}
(HERE/'SOURCES.json').write_text(json.dumps(rows, indent=2, sort_keys=True)+'\n')
print(json.dumps({'status':'SOURCES_FROZEN','count':len(rows),'root':str(ROOT)},indent=2))
