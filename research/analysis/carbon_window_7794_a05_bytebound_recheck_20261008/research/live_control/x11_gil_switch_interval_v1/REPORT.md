# GIL switch interval tracking for post-native XGetImage return delay

Task `X11-GIL-SWITCH-INTERVAL-20260916-001`, Issue #385.

**Disposition: `GIL_INTERVAL_TRACKING_SCOPED`.** This is a component-level causal discriminator. It shows that, under the same CPython interpreter with a CPU-bound competing Python thread, the delay after the native helper finishes tracks the interpreter switch interval. It does not establish a production setting, a live watcher speedup, input-release improvement, X server service time, or arbitrary-GUI reliability.

## Why this rung exists

Completed Issue #361 held the default 5 ms switch interval and found a median C-exit-to-Python-return delay of about 5.09 ms only when the competitor was a Python thread sharing the observer interpreter; an equivalent independent process did not reproduce that return delay. The smallest successor changes only `sys.setswitchinterval()` from 5 ms to 1 ms while keeping the same native XGetImage helper, observer CPU, competitor thread/core, Xvfb core, static pixels and acquisition schedule.

## Frozen design

Publication BASE: `b104db1b17fa717eecefca0209d243ca35332524`.

- 6 matched pairs / 12 cases / 384 acquisitions.
- 32 acquisitions per case.
- Arms: 5 ms versus 1 ms CPython switch interval.
- Same CPU-bound Python thread in both arms, on guest CPU1.
- Observer on guest CPU0; Xvfb on guest CPU2.
- Nominal 2 ms absolute start schedule; overdue slots are skipped rather than burst-caught-up.
- Counts by pair: 0, 511, 512, 513, 1023, 1024 exact BGRX target pixels.
- One formal block only; no retry, replacement, extension or post-data gate change.

Frozen gate: at least 4/6 matched pairs must have candidate median C-exit-to-Python-return <=2.0 ms **and** candidate/baseline ratio <=0.40.

The source-first freeze was posted to Issue #385 before formal execution. All source Git blobs were read back byte-exactly. Preformal mutation tests reject timestamp, switch-interval, affinity, pixel and decision mutations.

## Formal first outcome

All 6/6 matched pairs pass the frozen gate.

| metric | 5 ms arm | 1 ms arm |
|---|---:|---:|
| median of case medians: C-exit -> Python-return | 5.094800 ms | 1.082459 ms |
| range of case medians: C-exit -> Python-return | 5.087663–5.103363 ms | 1.079718–1.084847 ms |
| median of case medians: XGetImage internal | 82.725 us | 61.318 us |
| median of case medians: Python-before -> bytes-ready | 5.195830 ms | 1.156014 ms |

Matched candidate/baseline post-native ratios are 0.21202–0.21315; all six are below the frozen 0.40 gate. The approximately 5.09 ms -> 1.08 ms contraction is close to the manipulated interpreter scheduling quantum and strongly supports switch-interval dependence in this fixture.

This is not a direct measurement of GIL lock wait. `C-exit -> Python-return` includes GIL reacquisition, ctypes/libffi return processing and OS scheduling. `sys.setswitchinterval()` globally changes Python thread scheduling behavior, so the causal intervention is the interpreter switch interval, not an isolated lock primitive.

## Integrity and audit

- formal cases: 12/12 complete;
- acquisitions: 384/384;
- source/binary/schedule identity: PASS;
- exact pixel semantics: PASS;
- observer and competitor affinities: PASS;
- competitor CPU exposure and cleanup: PASS;
- Xvfb cleanup: PASS;
- frozen independent audit: PASS;
- unchanged preformal unit test after measurement: PASS.

Postformal negative controls over the real raw result reject five mutations: timestamp, switch interval, affinity, pixel payload and derived decision. No formal rerun or source rewrite occurred.

## Evidence retention

Formal raw JSON: 190,577 bytes, SHA-256 `9a4876108b3a6f25254b8fd033f0fa517ff16095b31840d518154128561a5a19`.

Exact XZ: 16,200 bytes, SHA-256 `6cb47870313e68c2a26c1f738528e98d3e8a8dece29390fa740237c8b3458132`. `raw.part00.b64` through `raw.part11.b64` concatenate to those XZ bytes losslessly; `decode.py` verifies both compressed and decoded digests.

## H / T / D / C / U

**H:** changing only the CPython switch interval from 5 ms to 1 ms under the same competing Python thread will proportionally reduce post-native return delay.

**T:** one source-first frozen 6-pair component block, 384 acquisitions, first outcomes only.

**D:** `GIL_INTERVAL_TRACKING_SCOPED`, because 6/6 matched pairs satisfy both frozen thresholds and all integrity gates pass.

**C:** the switch interval affects interpreter scheduling globally; reduced delay could reflect changed GIL scheduling plus related Python scheduling behavior rather than a pure GIL-reacquisition primitive.

**U:** one CPython 3.13.5 build, one Linux/Xvfb/libX11 stack, synthetic CPU-bound thread, guest CPU topology, unpinned frequency and a short serial allocation. No natural workload frequency or end-to-end task benefit is estimated.

## Next discriminator

Do not sweep more switch-interval values. The next useful rung is a separately frozen live-watcher integration under the same competing Python-thread condition: hold the watcher/predicate/input semantics fixed and compare 5 ms versus 1 ms switch interval on actual observation gaps and verified release. That tests whether this component-level headroom survives the live control path before any runtime/default-setting proposal.
