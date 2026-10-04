import json, importlib.util, shutil, platform, hashlib
from pathlib import Path
r={"scope":"dependency preflight only; no game/model/X11/input", "python":platform.python_version(),"modules":{k:bool(importlib.util.find_spec(k)) for k in ("vizdoom","PIL","Xlib","numpy")},"executables":{k:shutil.which(k) for k in ("Xvfb","wmctrl","xdotool","wslpath","node","codex")},"hardcoded_node_exists":Path("/mnt/c/Program Files/nodejs/node.exe").exists(),"wad_sha256":hashlib.sha256(Path("/data/freedoom2.wad").read_bytes()).hexdigest()}
Path("/out/dependency-preflight.json").write_text(json.dumps(r,indent=2)+"\n")
print(json.dumps(r),flush=True)
