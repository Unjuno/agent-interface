# Opt-in transport-to-PNG integration v2

This is a research candidate plus executable integration regressions. It does
not change shared defaults, the upstream decoder, GUI authority or any DOOM
allocation. Read `RETENTION_FAILURE.md` before interpreting timing claims.

## What is retained

- `freeze.json`: immutable source/plan hash commitment made before measurement.
- `candidate.py`: minimal repeat-path repair; the wire policy is unchanged.
- `../transport-revisit-v1/candidate.py`: byte-exact prior conversation control.
- `test_integration.py`: twelve real decoder/PNG-sink integration tests.
- `construction-validation.json`: new construction recheck, full stdout and
  exact source hashes; 12/12 PASS, not a performance rerun.
- `benchmark.py`: recovered original benchmark source for inspection. Its raw
  first result and plan file are MISSING; a plan digest is not the plan bytes.
- `RETENTION_FAILURE.md`: observed summary, missing artifact identities and
  FAIL_EVIDENCE_RETENTION. No `first-01.zip` is claimed to be retrievable here.

The prior v1 full ZIP remains a conversation attachment, SHA-256
`67af43beb5a317495de1277a48899ece29c2dbfcc275bdc2233ae1b686d29a35`.
Only its encoder is imported here. Historical v1 raw timings are not claimed to
be fully imported into GitHub. The v1 import keeps its source SHA-256
`fe6f935f32b9b3cc912c7cef9088d4da87df89fae44152e9aec48c3f04f717fc`.

## Run construction checks

From repository root, with CPython 3.13.5, NumPy 2.3.5 and Pillow 12.3.0 (the
measured environment also reported zlib 1.3.1):

```bash
python - <<'PY'
import hashlib,json
from pathlib import Path
p=Path('research/conditional_optimization/transport-integration-v2/freeze.json')
f=json.loads(p.read_text())
for path,expected in f['sources'].items():
    actual=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    assert actual==expected,(path,actual,expected)
print('All frozen source hashes match')
PY
python research/conditional_optimization/transport-integration-v2/test_integration.py
```

The tests use unchanged `research/observation_tiles/tile_transport.py`,
`image_artifact.py` and `research/observation_gating/exact_gate.py`.
They exercise real PNG files, but do not open a GUI, call a model or send input.
The tested contract is trusted, ordered, bounded local transport, not a hardened
network protocol. Corrupted/dropped local test packets fail without advancing
the decoder. Unchanged pixels may reuse a PNG while current action/context/time
metadata must still advance.

Do not execute the historical performance allocation again. A future measured
comparison requires a new ID and plan, and durable full-data checkpoint/readback
before any success promotion. The roadmap in `../ROADMAP_V2.md` names the next
retention, routing and real-caller gates. Correctness in this composition is not
proof of independent task success or model-token savings.
