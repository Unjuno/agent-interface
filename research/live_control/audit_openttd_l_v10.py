"""Audit unchanged v10 by source-pinned adaptation of the full v9 audit."""
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE / 'audit_openttd_l_v9.py'
BASE_SHA256 = 'd9833d481a2fe381651511b7ab23575781731fb4ed14e7e3d1c94fbe68016a99'


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise RuntimeError(f'expected one v9 audit patch site: {old[:80]}')
    return source.replace(old, new)


raw = BASE.read_bytes()
if hashlib.sha256(raw).hexdigest() != BASE_SHA256:
    raise RuntimeError('frozen v9 audit source changed')
source = raw.decode('utf-8')
patches = [
    ("results/timing-envelope-openttd-l-09", "results/timing-envelope-openttd-l-10"),
    ("{'x': 705, 'y': 240}, {'x': 673, 'y': 256}, {'x': 641, 'y': 272}",
     "{'x': 705, 'y': 239}, {'x': 673, 'y': 255}, {'x': 641, 'y': 271}"),
    ("assert len(observer) == 171", "assert len(observer) == 180"),
    ("assert transitions == [90, 131]", "assert transitions == [103, 143]"),
    ("observer[131:]", "observer[143:]"),
    ("(input_tokens, cached_tokens, output_tokens) == (151853, 91392, 1719)",
     "(input_tokens, cached_tokens, output_tokens) == (151842, 104448, 1880)"),
    ("model_wait_ms == 131033.9726 and feedback_ms == 19047.7812",
     "model_wait_ms == 139464.6532 and feedback_ms == 19490.6479"),
    ("'bounded_effect_memory_v9': 'success in 9 turns',",
     "'bounded_effect_memory_v9': 'success in 9 turns',\n            'unchanged_memory_v10': 'success in 9 turns',\n            'memory_candidate_live_summary': {'successes': 2, 'episodes': 2, 'zero_repeated_completed_segments': 2},"),
    ("'decision': 'RETAIN_LIVE_EFFECT_MEMORY_FOR_REPLICATION;_DO_NOT_PROMOTE'",
     "'decision': 'ADVANCE_EFFECT_MEMORY_TO_CHANGED_GEOMETRY;_DO_NOT_PROMOTE'"),
    ("'scope': 'one fresh same-task live episode; no causal speed, token, changed-geometry, human-tempo or cross-domain claim'",
     "'scope': 'unchanged second live memory episode; no causal speed, token, changed-geometry, human-tempo or cross-domain claim'"),
]
for old, new in patches:
    source = replace_once(source, old, new)
code = compile(source, str(Path(__file__).resolve()), 'exec')
exec(code, {'__name__': '__main__', '__file__': str(Path(__file__).resolve())})
