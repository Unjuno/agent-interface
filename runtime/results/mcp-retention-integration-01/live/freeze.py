import hashlib
import json
from pathlib import Path
import subprocess
from runtime.distribution_v2.build import SOURCE_FILES

root = Path(__file__).parent
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
manifest = {}
for name in (*SOURCE_FILES, 'runtime/backends/x11_v1/fixture_app.py'):
    data = subprocess.check_output(['git', 'show', revision+':'+name])
    target = root/'source'/name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    manifest[name] = hashlib.sha256(data).hexdigest()
(root/'FREEZE.json').write_text(json.dumps({'revision': revision, 'sources': manifest,
    'owner_sha256': hashlib.sha256((root/'owner.py').read_bytes()).hexdigest()}, indent=2))
(root/'PLAN.json').write_text(json.dumps({'task': 'type receipt-72 then save',
    'route': 'one public MCP stdio connection, primary decisions via files; no second model',
    'checks': 'view initial, validate draft, dispatch once, view result, retrieve by call_id without image, compare original raw report and input hashes, inspect saved effect after primary declaration',
    'limits': 'four decisions; no input replay; 300-second decision timeout; stop on unverified release',
    'scope': 'Tk private Docker composition, not registered host or six-task baseline. Caller source/binding fixed1/0, owner sets local runtime deadline. No model/token/host-visible latency claims.'}, indent=2))
