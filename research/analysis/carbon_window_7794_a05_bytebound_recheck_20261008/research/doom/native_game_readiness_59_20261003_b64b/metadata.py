import hashlib
import json
from pathlib import Path
import vizdoom as vd

root = Path(vd.__file__).parent
wad = root / "scenarios/basic.wad"
result = {
    "version": vd.__version__, "root": str(root),
    "basic_cfg": (root / "scenarios/basic.cfg").read_text(),
    "basic_wad_sha256": hashlib.sha256(wad.read_bytes()).hexdigest(),
    "basic_wad_bytes": wad.stat().st_size,
    "engine_sha256": hashlib.sha256((root / "vizdoom").read_bytes()).hexdigest(),
    "wheels": Path("/opt/wheels.sha256").read_text(),
    "python": Path("/opt/python-manifest.txt").read_text(),
    "dpkg": Path("/opt/dpkg-manifest.txt").read_text(),
}
print(json.dumps(result, sort_keys=True))
