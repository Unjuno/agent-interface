"""Read-only exact Git source export; never checks out or edits the shared clone."""
import hashlib, json, pathlib, platform, shutil, subprocess, sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parent / 'agent-interface'
BASE = '3e93df3755b8ae8e2e063ed8f61524989e4bf3df'
HEAD = 'dbe05f5ce33b6827dbd3d09e8a85da1e2d20f51a'
FILES = ['primary_stdio.mjs','primary_exchange.mjs','primary_caller.mjs','relay_host.mjs','relay_client.mjs']
def git(*args):
    return subprocess.check_output(['git',*args], cwd=REPO)
def digest(b):
    return hashlib.sha256(b).hexdigest()
def put(path, b):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as f: f.write(b)
images = []
for arm, commit in [('baseline',BASE),('candidate',HEAD)]:
    for name in FILES:
        path = 'runtime/host_v1/' + name
        b = git('show', commit+':'+path)
        put(ROOT/'source'/arm/name,b)
        images.append(dict(arm=arm,commit=commit,path=path,blob=git('rev-parse',commit+':'+path).decode().strip(),bytes=len(b),sha256=digest(b)))
patch = git('diff',BASE,HEAD,'--',*['runtime/host_v1/'+n for n in FILES])
put(ROOT/'source-diff.patch',patch)
assert patch.count(b"+  lines.on('error',failed);") == 1
assert sum(x.startswith(b'+') and not x.startswith(b'+++') for x in patch.splitlines()) == 1
assert all(images[i]['sha256'] == images[5+i]['sha256'] for i in range(1,5))
node = pathlib.Path(shutil.which('node')).resolve()
python = pathlib.Path(sys.executable).resolve()
record = dict(schema='accepted-child-source-v1',utc=datetime.now(timezone.utc).isoformat(),base=BASE,head=HEAD,images=images,
  platform=platform.platform(),node=dict(path=str(node),version=subprocess.check_output([str(node),'--version']).decode().strip(),sha256=digest(node.read_bytes())),
  python=dict(path=str(python),version=platform.python_version(),sha256=digest(python.read_bytes())),
  mcp_sdk_present=__import__('importlib.util',fromlist=['find_spec']).find_spec('mcp') is not None,
  maximum_children=2,maximum_deck_seconds=100,maximum_output_bytes=1048576)
put(ROOT/'SOURCE.json',(json.dumps(record,indent=2)+'\n').encode())
print(json.dumps(dict(exported=len(images),base=BASE,head=HEAD,node=record['node']['version'],mcp_sdk_present=record['mcp_sdk_present'])))
