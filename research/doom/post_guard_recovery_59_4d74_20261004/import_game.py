import vizdoom, json, hashlib
from pathlib import Path
r={'scope':'native library import only; no DoomGame instance/session/model/X11/input','version':vizdoom.__version__,'module':vizdoom.__file__,'module_sha256':hashlib.sha256(Path(vizdoom.__file__).read_bytes()).hexdigest()}
Path('/out/result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
