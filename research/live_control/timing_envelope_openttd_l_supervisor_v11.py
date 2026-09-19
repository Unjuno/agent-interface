"""Changed-geometry allocation of the source-pinned v9 effect-memory policy."""
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE / "timing_envelope_openttd_l_supervisor_v9.py"
BASE_SHA256 = "d09a68e9680b7a42e7f4ab5f6315142aa843bd7983c1676978ae23ccc7547e2e"

raw = BASE.read_bytes()
if hashlib.sha256(raw).hexdigest() != BASE_SHA256:
    raise RuntimeError("frozen v9 L supervisor source changed")
source = raw.decode("utf-8")
replacements = [
    ("'timing_envelope_openttd_l_supervisor_v9.py','timing_envelope_openttd_l_driver_v6.py'",
     "'timing_envelope_openttd_l_supervisor_v11.py','timing_envelope_openttd_l_driver_v7.py'", 1),
    ("linux(HERE/'timing_envelope_openttd_l_driver_v6.py'),arm,'timing-envelope-openttd-l-09'",
     "linux(HERE/'timing_envelope_openttd_l_driver_v7.py'),arm,'timing-envelope-openttd-l-11'", 1),
    ("base=HERE/'results/timing-envelope-openttd-l-09'",
     "base=HERE/'results/timing-envelope-openttd-l-11'", 1),
    ("'scope':'fresh seed-991003 OpenTTD five-tile L objective with one bounded unresolved-drag effect memory'",
     "'scope':'fresh seed-991004 changed-geometry five-tile L objective with unchanged bounded effect memory'", 1),
]
for old, new, count in replacements:
    if source.count(old) != count:
        raise RuntimeError(f"unexpected v9 supervisor patch count: {old}")
    source = source.replace(old, new)
insertion = (
    "    (\"'seed_semantics':'byte-pinned seed-991003 save; target tiles 977,978,979,1043,1107; closed toolbar'\",\n"
    "     \"'seed_semantics':'byte-pinned seed-991004 save; target tiles 684,685,686,750,814; closed toolbar'\"),\n"
)
marker = "    ('from openttd_effect_sheet_v1 import build as build_effect_sheet',\n"
if source.count(marker) != 1:
    raise RuntimeError("v9 patch insertion marker changed")
source = source.replace(marker, insertion + marker)
code = compile(source, str(Path(__file__).resolve()), "exec")
exec(code, {"__name__": "__main__", "__file__": str(Path(__file__).resolve())})
