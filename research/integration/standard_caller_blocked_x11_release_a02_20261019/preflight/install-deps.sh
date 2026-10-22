set -eu
python3 -m pip install --disable-pip-version-check mcp==1.30.0 python-xlib==0.33 pillow==13.0.0
python3 -c 'import sys,shutil,json,importlib.metadata as m; print(json.dumps({"python":sys.version,"xlib":m.version("python-xlib"),"pillow":m.version("pillow"),"mcp":m.version("mcp"),"xvfb":shutil.which("Xvfb")},sort_keys=True))'
python3 -m pip freeze
