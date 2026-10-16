"""Unchanged replication wrapper for the source-pinned v9 live-memory allocation."""
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE / 'timing_envelope_openttd_l_supervisor_v9.py'
BASE_SHA256 = 'd09a68e9680b7a42e7f4ab5f6315142aa843bd7983c1676978ae23ccc7547e2e'


raw = BASE.read_bytes()
if hashlib.sha256(raw).hexdigest() != BASE_SHA256:
    raise RuntimeError('frozen v9 supervisor source changed')
source = raw.decode('utf-8')
replacements = [
    ('timing_envelope_openttd_l_supervisor_v9.py',
     'timing_envelope_openttd_l_supervisor_v10.py', 1),
    ('timing-envelope-openttd-l-09', 'timing-envelope-openttd-l-10', 2),
]
for old, new, expected_count in replacements:
    if source.count(old) != expected_count:
        raise RuntimeError(f'unexpected v9 replication patch count: {old}')
    source = source.replace(old, new)
code = compile(source, str(Path(__file__).resolve()), 'exec')
exec(code, {'__name__': '__main__', '__file__': str(Path(__file__).resolve())})
