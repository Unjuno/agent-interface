#!/usr/bin/env bash
# Environment preparation ONLY. No generated route, model, game or X11 input.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends python3-venv libgl1 libglu1-mesa libsdl2-2.0-0 libopenal1 ca-certificates
python3 -m venv --system-site-packages /opt/owner-measurement-env
/opt/owner-measurement-env/bin/python -m pip install --only-binary=:all: --no-cache-dir \
    --report /opt/owner-measurement-install-report.json 'vizdoom==1.3.0'
/opt/owner-measurement-env/bin/python -c 'import importlib,json; rows=[]
for name in ("Xlib","PIL","numpy","vizdoom"):
 module=importlib.import_module(name)
 rows.append({"module":name,"file":module.__file__,"version":getattr(module,"__version__",None)})
print(json.dumps({"scope":"dependency-import-only-no-native-or-game","rows":rows},sort_keys=True))'
