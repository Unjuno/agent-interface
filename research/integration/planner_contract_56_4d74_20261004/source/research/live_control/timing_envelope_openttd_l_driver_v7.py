"""Source-pinned changed-geometry adaptation of the durable L driver v6."""
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE / "timing_envelope_openttd_l_driver_v6.py"
BASE_SHA256 = "77977cafe810cc1a13773d4e19d7cb707fc3d94e8ee29b589fa4fa40ebe63717"


raw = BASE.read_bytes()
if hashlib.sha256(raw).hexdigest() != BASE_SHA256:
    raise RuntimeError("frozen v6 L driver source changed")
source = raw.decode("utf-8")
replacements = [
    ("'timing_envelope_openttd_l_driver_v6.py'", "'timing_envelope_openttd_l_driver_v7.py'", 1),
    ("pointer_socket_entry_v8.py", "pointer_socket_entry_v9.py", 2),
    ("byte-pinned seed-991003 save; five-tile L objective", "byte-pinned seed-991004 changed-geometry save; five-tile L objective", 1),
]
for old, new, count in replacements:
    if source.count(old) != count:
        raise RuntimeError(f"unexpected v6 driver patch count: {old}")
    source = source.replace(old, new)
code = compile(source, str(Path(__file__).resolve()), "exec")
exec(code, {"__name__": "__main__", "__file__": str(Path(__file__).resolve())})
