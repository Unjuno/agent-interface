# O2 memory envelope: exact retained m7q3 evidence

Issue #4402; evidence-only delivery after closed #4139. This publishes the
already executed `o2-memory-m7q3-local-20260925-01` allocation. It is NOT public
preregistration, a new measurement, or production adoption. The original local
freeze, results and publication-unavailable record remain byte-for-byte intact
inside the capsule. #4340's dense route and #4362's streaming compressor are
separately owned; neither is implemented or rerun here.

## Retained result

**PASS_LOCAL_MEMORY_NONREGRESSION**, at the original six-condition scope.
All54 measurements and three batch exits reconcile. Contiguous O2 and the
one-line strided comparator have exact initial/update packet parity. All six
median extra-traced-peak differences are0 bytes. A single small LOCAL sample
is45 bytes lower with contiguous materialization; individual counters are not
claimed identical. The declared allowance was77824 bytes, not a proven bound.

Dense update medians, in bytes (three fresh processes per cell):

| RGB geometry | O1 full | O2 strided | O2 contiguous | Full wire chosen by all |
|---|---:|---:|---:|---:|
| 641x479 |302715|2164046|2164046|7354|
| 1281x721 |302717|5961452|5961452|21127|
| 2561x1441 |368344|24115336|24115336|82911|

Dense ranges equal their medians. LOCAL O2 wire packets are smaller than O1;
this does not justify always reverting to O1. The full original table, ranges,
raw frames/packets, /proc samples and all54 worker records are retained.

## H / T / D / C / U

H: contiguous materialization preserves bytes without exceeding the strided
median update traced peak by77824 bytes at any fixed condition.

T: three geometries x LOCAL/DENSE x O1_FULL/O2_STRIDED/O2_CONTIGUOUS x three
fresh processes, in three immutable18-worker batches. Input creation, imports
and initial encoding precede tracing. All54 worker and three batch exits0;
no measurement retry, replacement or exclusion. The comparator changes only
`np.ascontiguousarray(tile).tobytes()` back to `tile.tobytes()` in current source.

D: exact source/input/packet/decoded-pixel/process reconciliation, all six
memory gates, separate raw-only audit and12 effective corruption controls
passed. Four original construction tests passed. This continuation restores
and re-audits only; it starts zero measurement workers.

C: one compressible synthetic RGB family and one exact implementation stack.
O2 builds tile candidates before selecting the smaller wire packet. O1 versus
O2 changes the whole strategy; it is not isolated internal cost attribution.
Same-author separately implemented auditor is not external human review.

U: tracemalloc update allocations are not all native allocations or whole
process peak RSS. Preloaded input is excluded. VmHWM covers earlier process
lifetime and cannot isolate update cost. Three technical repeats are descriptive
median/range, not population confidence intervals. No held-out GUI, concurrent
encoder, memory-pressure, model/task/token, latency, cross-platform or product
claim. No calibrated physical uncertainty is invented.

Environment: provided Linux x86_64 container, CPython3.13.5, NumPy2.3.5,
zlib1.3.1, guest AMD EPYC9V74, CPU0 affinity, batch1, frequency not fixed.
Docker/OrbStack image identity was unavailable. No GUI/input/model/provider,
installation or experiment-network calls occurred.

## Complete original bytes and chronology

Original local freeze:2026-09-25T12:38:27.834250Z. Original base4a1f3957e91b412a64769199f78f2c4b0102d28b;
publication intake4c701cc51b06296268ad8d9ae3eff1dd6f2d379d.
Canonical codec remains Git blob0de27f79e6cbf5ded545430b26a87dcacc142b71.

The22 binary parts concatenate to an88088-byte TAR.XZ, SHA256
`222d530df57bb1bd9e3cf7aed99dece1c1d039812fe5b07bcf7d8432151c6820`.
It restores **all457 originals /63114042 member bytes**, including source,
plans, construction, input RGB, initial/update packets, raw counters/exits,
auditor, original report and publication STOP. TAR metadata alone is normalized.
Original ZIP787699 bytes, SHA256
`8fb3c3f223e037452aedec0a42f287a4627e13bb504bdb5506f90851fb29a035`.
The ZIP container itself is not published; every original member content is.

Issue4402 initially mistyped the ZIP size as788153; comment5841132223 corrected
it before publication. No original bytes or scientific outcome changed.
Each uploaded binary blob ID matched its local exact-byte Git object.
Reachability, current-head CI and merge/readback are separate delivery gates;
object creation or a local audit alone does not establish those gates.

## Read-only reproduction

From this directory, with CPython3.13 standard library:

```sh
python -S -B verify.py
python -S -B test_restore.py
python -S -B restore.py /tmp/m7q3-fresh-review
```

The last command requires a new destination under a trusted, quiescent parent.
The restorer bounds decompression, verifies all456 original manifest entries
plus the manifest, and executes no restored code. `verify.py` explicitly invokes
only the retained read-only auditor, never worker.py/run_batch.py. Its output
must report54 rows, byte-identical AUDIT,12 corruption rejections and zero new
measurement workers. Ten packaging tests (one positive,nine refusals) pass.
Do not rerun the consumed measurements. Hashes are integrity, not authentication.

## Integration handoff

For #2789 observation/preparation, budget transient candidate staging separately
from final wire size. This narrows #4139's unmeasured resource boundary but does
not adopt any new encoder, set a general RAM limit, or complete the desktop
acceptance/ROADMAP. All repository additions stay under this namespace.
