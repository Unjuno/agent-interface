# Evidence-dependent compute: X11 PNG preparation calibration R6

Issue #1784. Fresh live transfer from #1765's synthetic calibration fixture to a real private-X11 current-frame PNG preparation job.

Decision: **PASS_EVIDENCE_COMPUTE_X11_PNG_CALIBRATION_SCOPED**.

## Frozen construction
The pre-existing source-first bundle was restored byte-exact against `SOURCE_MANIFEST.json`.
- full prepare median: **79.513029 ms**
- eligible reveal candidates: 2/5/8/12 ms
- frozen reveal: **12 ms**
- probe correctness4/4
- invalidated RUN stale detection / positive obsolete work1/1

No source changed before formal.

## Formal first outcome
One formal invocation; reruns/replacements/tuning0.
- 32 matched scenarios /64 active executions
- 24 STABLE /8 INVALIDATE; authored p=1/4
- decoded current-generation PNG correct64/64
- stale-current publication0
- invalidated RUN stale detection8/8
- invalidated RUN positive obsolete CPU8/8

Frozen utility `C = completion_wall_ns + obsolete_cpu_ns`:
- stable WAIT loss g mean **14.726061 ms**
- invalidation RUN waste w mean **160.437650 ms**
- break-even p*≈**0.084070271**

Authored p=0.25 > p*, therefore the calibrated selector predicts **WAIT**.

Direct aggregate independently agrees:
- RUN total **4127.933901 ms**
- WAIT total **3197.858154 ms**
- WAIT advantage **930.075747 ms**
- threshold policy WAIT; direct policy WAIT.

Cache/currentness:
- 48 REUSE /8 REBUILD_REQUIRED /8 DROP_EXPIRED
- authored reuse rate3/4
- 60,000 actual X11 generation-property reads
- p50 30,146 ns; p95 41,423 ns; max4,796,751 ns

Independent audit errors[]; corruption controls6/6 reject.

## Evidence retention
Exact formal RAW: 823,823 bytes; SHA-256 `55d099ba71925692560d9b81e9ee65c39027af14133936b7d14026bf02a82e36`.
Deterministic gzip SHA-256 `862219f6e864e8836e661fcc33bd22f470e4ff5ebf849f74bc02c84936225415`.
Audit SHA-256 `14c43ae6a246f59481345582038c4df2fa82a26822cd68c21c90d633b25a1d29`.

## Interpretation
The synthetic #1765 fixture favored RUN under its authored workload; this private-X11 PNG population favors WAIT under its own authored workload. Scheduler policy is therefore population/cost dependent, not a universal preference for background computation.

The authored p=1/4 and reuse=3/4 are fixture frequencies, not deployment estimates. Absolute PNG/property timings are Xvfb/Pillow/zlib/host specific. No model/token/human-tempo/cross-platform/product claim.
