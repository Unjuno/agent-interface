# Same-timestamp cancellation boundary — #6501

**PASS_BOUNDARY_CHARACTERIZATION_SCOPED.** The finite model requires an explicit
ordering of cancellation and delivery when their clock values coincide. This
does not establish a runtime flaw or revoke the retained T0b scoped result.

| Comparator | Wrong admissions | Wrong rejections | Decisions |
|---|---:|---:|---:|
| Exact retained T0b timestamp `<` helper | 48 | 0 | 384 |
| Conservative timestamp `<=` comparison | 0 | 48 | 384 |
| Explicit per-waiter event ordering | 0 | 0 | 384 |

One frozen candidate invocation and one separately coded raw-only auditor each
exited 0. Retry count 0. The auditor reconciled all 192 finite assignments / 384
waiter decisions and rejected 8/8 effective copied-output mutations. These are
exhaustive synthetic assignments, not independent trials or empirical error rates.
Six construction/regression tests passed; the first stub's two expected failures
and the pre-freeze tuple/list construction error are described in preregistration.

Example: cancel-a and return both have synthetic timestamp 5 ms. If cancel-a is
ordered first, a must receive CANCELLED_WAITER. If return is ordered first, a
receives ADMISSIBLE_TRUE. The timestamp-only helper returns ADMISSIBLE_TRUE in
both cases. Changing only `<` to `<=` rejects both cases instead. Caller b's
independent cancellation state remains separate despite the shared read result.

## Provenance and execution

- Base main: 11f1bae6f8dbfd280b6ccbd0def0bc23fa5da68d.
- Published source freeze: 92d1f99bd4e5f015f93195a00636df6eb4419256.
- Allocation: 6501-CANCEL-ORDER-HOST-20261003-01a0ff2d.
- Start/end: 2026-10-03 00:46:13.013080 / 00:46:13.368943 UTC.
- Host: Windows 11 build 26200, CPython 3.12.10, stdlib, one process at a time.
- Command: `python -B run_once.py` in this package's dedicated local copy.
- RUN.json records actual argv, child process exits, clocks and source/raw hashes.
  Candidate elapsed 110,510,300 ns; auditor 152,710,900 ns, including process
  startup. These single durations are provenance only, not a route-performance
  or latency estimate. Host free memory was about 729 MiB at intake; storage was
  constrained and changed during other activity. No controlled-load claim.
- Raw SHA256: 60759e1b49d03a7d83bb3968b892c2c349f7e89842f17aa645043785421a580b.
- Audit SHA256: f9d763715b9b4c1f85b9b25f42f9c73868a50f4ec116530a3681dc15bf4c873a.

All frozen source files were read back from the published freeze and compared
exactly with local text. Retained candidate has exact original Git blob identity
473529819d9fe6dec29cf113bd49a2c7de872236, 4,338 bytes. Only `_classify` is called;
the original scheduler/run/main are never executed. Historical artifacts are
unchanged. No container, WSLc, GPU, model, GUI or physical input was invoked.

## Byte-preserving raw recovery and verification

The original candidate raw is retained locally. For compact publication its exact
bytes are stored in `run01/candidate-raw.json.gz.b64`; this is a reversible gzip
container, not selected or edited rows. Decode into a fresh directory:

```python
import base64, gzip, hashlib
from pathlib import Path
encoded = Path('run01/candidate-raw.json.gz.b64').read_bytes()
raw = gzip.decompress(base64.b64decode(encoded))
assert hashlib.sha256(raw).hexdigest() == '60759e1b49d03a7d83bb3968b892c2c349f7e89842f17aa645043785421a580b'
with Path('recovered-candidate-raw.json').open('xb') as f:
    f.write(raw)
```

Read-only audit reproduction on those recovered bytes may use a fresh output:
`python -B auditor.py recovered-candidate-raw.json 9f389bf99882f7107ff41902474e9e2d6699667b65eabcd5cd5b7f97f1e158ba fresh-audit.json`.
This re-audits retained raw; it does not rerun the candidate allocation.
Construction tests: `python -B -m unittest -v test_boundary test_auditor`.

## Decision and remaining limits

Retain this finite counterexample and comparator. A future real implementation
must bind a caller-local cancellation state to the delivery/admission instant,
or report uncertainty when ordering cannot be observed. Do not fabricate a
global sequence from wall-clock labels. A conservative cancel-on-tie policy is
safe under this finite contract but sacrifices eligible delivery opportunities.
Per-caller action admission remains necessary; a shared descriptive result is
never another caller's capability or effect proof.

The order-aware implementation is a construction reference only. There is no
GUI effect, distributed linearizability, production-safety, physical-release or
efficiency conclusion. No runtime or acceptance gate is changed. The old T0b may
have a return-first equality convention; the new test deliberately expands the
model to both admissible intra-bucket orders.

Publication is a reviewable PR; main reflection remains pending FINAL-v5's
non-author content approvals, integration check and controlled apply. No hosted
CI or repository-wide suite success is inferred from the scoped checks.
