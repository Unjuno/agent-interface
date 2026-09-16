# Live native ROI predicate integration at fixed 2 ms cadence

Task `QUIET-WATCH-NATIVE-PREDICATE-INTEGRATION-20260916-001`, Issue #270.

**Disposition: `PASS_INTEGRATION_SCOPED`.** This is a scoped live-X11 integration result only. It does not modify or promote the shared runtime.

## Question

The preceding native-acquisition study (#236 / merged evidence PR #257) held a 2 ms nominal watcher cadence and replaced Python-Xlib acquisition with native libX11 `XGetImage`. Correctness passed, but the frozen acquisition-cost gate held at `HOLD_COST_GATE`. The following primitive study (#252 / PR #266) then isolated the remaining Python ROI predicate and found a large exact-count microbenchmark win for a CPython C extension.

This experiment advances exactly one rung: **both arms use the same native `XGetImage` acquisition path and differ only in how the returned 4096-byte 32x32 BGRX ROI is counted.**

Baseline: retained Python four-byte-step exact-BGR loop.

Candidate: retained exact native CPython bytes-in/count-out predicate.

The target colour remains BGR `(50, 50, 220)` and the decision remains full exact count `>= 512`. No early threshold exit, ROI shrink, subsampling, shared-memory acquisition, latch, model call or shared-runtime edit is introduced.

## Source-first construction and freeze

Publication base: `a08cbd02e284d2dc9bf000f9daa3b673a230b07e`.

Frozen pre-formal branch head: `149717fdbeecbbb2f48b744e86a9557c0a98bd3e`.

The retained dependencies are exact copies of earlier sources:

- native acquisition source Git blob `447233bba1819528e7b9c34cdbb36af3b4686bc6`;
- native predicate source Git blob `e05bbd069cc087ca4ce023b42a45e3e652cc72c2`;
- upstream live fixture runner Git blob `64bd892826cba9f7d436cc37c3b4e1aa87101909`.

Frozen binary SHA-256:

- native acquisition: `e4e9262ec553f1244d3e781caddb496ae1ac9dae0607451e3cf75422e07305bc`;
- native predicate: `fb091f2997882c664e740d90c8f5f1c8a8f64d86410ede851a08105aa01e1d3d`.

Preregistration SHA-256 is `99c777e7bcda8b13a7b0ebf98e3a3accba53eb3872395b2746da5a78cae9d6e9`; the exact schedule SHA-256 is `c1023f244915d93a2cc1a3c334040d9e0ff9f39bc11b676006b957b1b8c59b23`.

Three construction attempts are retained separately from the formal block. The first stopped because Tk had no `DISPLAY`; the second stopped because the installed `python3-xlib 0.15` required an explicit Xauthority path even with Xvfb `-ac`; no formal case ran. The third used private Xvfb `:96`, `640x400x24`, `-ac -nolisten tcp`, plus an explicit empty Xauthority file. It passed static rendered counts 0/1/511/512/513/1023/1024, native acquisition argument guards, native predicate length/type guards, and four excluded live target/nuisance cases. Construction timing was not used to tune formal gates.

## Formal allocation

One serial 38-case block ran exactly once:

- 15 target cases per arm: three repetitions at 150, 152, 154, 156 and 158 ms onset offsets;
- 4 nuisance cases per arm at 150, 152, 154 and 156 ms;
- nominal watcher cadence 2 ms;
- nominal cue duration 5 ms;
- XTEST Right key input;
- 600 ms owner deadline;
- balanced arm order within target and nuisance classes;
- no retry, replacement or extension.

Full acquisition/count brackets, current-thread CPU, raw ROI payloads, cue timing, app press/release, final ROI and independent X11 keymap release are retained.

## Frozen decision gates and result

| gate | frozen requirement | result |
| --- | ---: | ---: |
| target detection | 15/15 each arm | **15/15, 15/15** |
| nuisance false cancel | 0/4 each arm | **0/4, 0/4** |
| input/final/source/raw integrity | all pass | **PASS** |
| median paired observation thread-CPU ratio | native/Python <= 0.80 | **0.2896468** |
| median paired observation wall ratio | native/Python <= 0.90 | **0.4729108** |
| median paired max-gap ratio | native/Python <= 1.10 | **1.0979277** |

Decision: **`PASS_INTEGRATION_SCOPED`**.

The CPU and wall reductions are large in this exact fixture. Median nuisance totals were:

| measurement | Python count | native count |
| --- | ---: | ---: |
| acquisition-only wall | 24.309 ms | 21.495 ms |
| acquisition-only thread CPU | 10.044 ms | 8.777 ms |
| counting wall | 22.131 ms | 0.441 ms |
| counting thread CPU | 22.290 ms | 0.606 ms |
| complete observation wall | 46.733 ms | 22.144 ms |
| complete observation thread CPU | 32.162 ms | 9.360 ms |
| max count-end -> next-start gap | 2.198 ms | 2.287 ms |
| acquisition count | 302 | median 302 (302,302,298,302) |

The integration result therefore supports the narrower causal story that the Python predicate was a material component of observer cost. It does **not** show that all observer timing becomes better.

## Important max-gap qualification

The max-gap gate passed only narrowly: median paired ratio `1.0979277` against the frozen `<= 1.10` boundary. The four pair ratios were `1.0417`, `1.1542`, `1.5478`, and `0.7390`; two of four candidate pairs were worse than 1.10, and one candidate nuisance case reached a 3.591 ms max gap with 298 samples.

Accordingly this result is **not evidence of robust scheduler-gap improvement**. It only passes the exact frozen median gate. This is the highest-information uncertainty for the next rung.

## Cue and release timing

The candidate did not produce a material descriptive shift in the target timing endpoints:

- Python cue draw-completion median 5.290 ms; native-count median 5.318 ms.
- Python cue-to-app-release median 2.236 ms; native-count median 2.237 ms.

Thus the large computation reduction did not turn into a detectable release-latency improvement in this small synthetic block. Software draw-completion timestamps are not physical scanout times.

## Raw retention

Formal `raw.json` is 2,096,165 bytes, SHA-256 `07533a59ab969f3cbde6bb40a4f244d2146d79698c3af179424de3e6b87a0599`.

Its lossless zlib representation is 259,371 bytes, SHA-256 `cfcb335fd4a482ae6be31e6bcbe462cc6fc24f45b53b1415d468a24a70316868`. It is retained as eight Base64 text parts. `decode_artifacts.py` concatenates the parts, verifies compressed and decoded hashes, and also reconstructs the two exact executed native binaries.

This closes the raw-retention failure mode from the older #231 publication for this new allocation; it does not retroactively reconstruct #231 raw bytes.

## Audit finding

The frozen independent audit passes all declared semantic/safety/source/schedule/cost checks. Negative controls show that it rejects stored match-count mutation, source-hash mutation and release-verification mutation. It does **not** independently authenticate a one-nanosecond mutation of a stored timing field: its checks validate timing ordering and recompute the metrics, but without a pre-existing raw-byte commitment an internally coherent tiny timing edit remains acceptable.

That limitation is retained rather than rewriting the frozen audit after measurement. Additive `audit_strict_posthoc.py` pins the immediately recorded formal raw SHA-256, zlib SHA-256, preregistration, frozen audit source and frozen audit result; it then reruns the frozen audit. The real result passes and all four retained mutations fail the posthoc tamper-evidence gate. This posthoc layer improves retention integrity but is not relabelled as preregistered evidence.

## H / T / D / C / U

**H.** With acquisition held native and identical, exact native counting can preserve target/nuisance and release correctness while reducing full-window observation CPU by at least 20%, wall by at least 10%, and not degrading the median paired maximum sampling gap by more than 10%.

**T.** One source-first-frozen, 38-case private-Xvfb allocation; 15 targets + 4 nuisances per arm; one material factor changed; first outcomes only; raw pixels retained losslessly.

**D.** `PASS_INTEGRATION_SCOPED` under the exact frozen gates. No shared-runtime promotion follows automatically.

**C.** X server latency, host scheduling, GIL/ctypes behavior and source-side Tk scheduling can dominate individual gaps. Lower Python compute can coexist with worse individual scheduling gaps, as observed in two nuisance pairs.

**U.** One synthetic Xvfb fixture, four nuisance pairs, CPU frequency unpinned, software draw timestamps, research-local input owner and one host. No hard-real-time, arbitrary-GUI, gameplay, end-to-end agent or production safety claim follows.

## Next staged question

Do **not** add another optimization or edit the shared runtime yet. The next rung should change no mechanism: run a fresh, separately frozen nuisance-only replication of these two exact arms with more full-window pairs and a new schedule, to determine whether the near-boundary max-gap result is stable or was a small-n scheduling fluctuation. Only if that replication preserves correctness and closes the gap uncertainty should this path be considered for a shared-runtime implementation gate.
