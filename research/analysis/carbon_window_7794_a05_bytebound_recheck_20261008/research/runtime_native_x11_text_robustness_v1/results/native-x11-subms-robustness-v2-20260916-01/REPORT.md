# Native X11 sub-ms robustness v2 — retained completed result

**Result ID:** `native-x11-subms-robustness-v2-20260916-01`  
**Frozen V2 source/head:** `db051e9f6709c2000bc892153969b80e983abc88`  
**V1 predecessor:** `native-x11-subms-robustness-v1-20260916-01` — `INCOMPLETE_OUTER_TIMEOUT`, never resumed or pooled.

## Disposition

**ROBUST_CANDIDATE / RETAIN_1_0MS_REQUESTED / DO_NOT_GENERALIZE**.

V2 preserved V1's scientific conditions and changed only orchestration: five counterbalanced checkpoint batches, four fresh Calc sessions per batch, giving five new sessions for each requested delay `0.8 / 0.9 / 1.0 / 1.1 ms`. Every V2 session executed exactly once. V1 completed sessions are excluded from all V2 counts.

| requested pacing | exact sessions | total exact strings | median measured char-start | median edit interval | gate |
| ---: | ---: | ---: | ---: | ---: | :---: |
| 0.8 ms | 0/5 | 45/80 | 0.875381 ms | 154.179 ms | FAIL |
| 0.9 ms | 2/5 | 77/80 | 0.983232 ms | 176.030 ms | FAIL 5/5 |
| **1.0 ms** | **5/5** | **80/80** | **1.074621 ms** | **182.788 ms** | **PASS** |
| 1.1 ms | 5/5 | 80/80 | 1.163625 ms | 201.780 ms | PASS |

The conservative frozen gate defines `ROBUST_CANDIDATE` as the lowest requested delay with **5/5 eligible exact sessions** and all control gates. Therefore the retained candidate is **1.0 ms requested pacing**.

This is not a statistical reliability guarantee and not a universal timing constant. It is a bounded engineering gate in this Linux/Xvfb/Openbox/LibreOffice Calc/XTest setup.

## Failure structure

All 20 sessions passed transport/freshness/release controls. Semantic errors are therefore not reclassified as transport failures.

- 0.8 ms exact counts: `8, 10, 9, 10, 8` / 16. Repeated-character collapse is pervasive (`office→ofice`, `bookkeeper→bokkeeper`, shortened repeated-letter stress strings, etc.).
- 0.9 ms exact counts: `15, 15, 16, 15, 16` / 16. It is **intermittent**, not robust under the 5/5 gate. Retained failures include `office→ofice`, one `office→oldffice`, and one repeated-`t` collapse.
- 1.0 ms and 1.1 ms: every session 16/16 exact.

The measured char-start interval is not identical to the requested post-character delay. At requested 1.0 ms, the five-session median of session medians is 1.074621 ms. Treat requested pacing as backend policy input and measured intervals as execution evidence.

## Source / builder closure

Before V2 execution in the continuing session:

- V2 files `PLAN_V2.md`, `run_batch_v2.py`, `aggregate_v2.py`, `test_v2.py`, `build_precise.py`: **5/5 Git-blob match** against frozen head `db051e9f...`;
- frozen dependency blobs: **4/4 exact** (`go.mod db4cfa...`, `backend_text.go 157a240...`, `backend_text_test.go 9dcc33...`, controller source `565494...`);
- generated precise busy-wait backend blob: exact `a766205e0c75288e3583f45ba2b58b58f7aca951`;
- Go tests PASS;
- generated controller SHA-256: `28024b4ad85ee5bf9a09546af01503ea1c583a5a666658f00f5f70b541070b7e`;
- V2 static tests: 4/4 PASS.

No source condition was changed after execution started.

## Execution / retention

Fixed batch order:

1. `0.8, 0.9, 1.0, 1.1`
2. `1.1, 1.0, 0.9, 0.8`
3. `0.9, 1.1, 0.8, 1.0`
4. `1.0, 0.8, 1.1, 0.9`
5. `1.1, 0.9, 1.0, 0.8`

Each completed batch was checkpointed before the next was consumed. The final aggregate was run once after all five batch receipts existed. Formal reruns: **0**.

Independent posthoc audit re-read all 20 report/score/execution receipts and all 20 XLSX files, verified output SHA-256, verified every XLSX ZIP archive with no CRC failure, recomputed condition counts, and reproduced `robust_candidate_ms = 1.0`.

No model/provider/network calls were used.

## H/T/D/C/U

**H:** the prior 1 ms candidate has a measurable robustness margin over 0.9 ms when the native tight loop is repeated across fresh sessions.  
**T:** 20 fresh source-frozen Calc sessions, counterbalanced in five four-session batches, same 16-string corpus, precise busy-wait implementation, independent workbook scorer, stale zero-input and terminal-release gates.  
**D:** `ROBUST_CANDIDATE` at 1.0 ms requested because 1.0 and 1.1 are 5/5 exact while 0.8 is 0/5 and 0.9 only 2/5.  
**C:** host scheduling, Xvfb/Openbox/XTest, LibreOffice, locale/input stack, corpus composition, and the busy-wait implementation can shift the boundary.  
**U:** one host/container and one application family; no WSLg/Xwayland, Wayland, native Windows/macOS, Unicode/IME, power/CPU-cost accounting, or statistical reliability guarantee.

## Successor

Do **not** narrow below 1.0 ms on this same fixture merely to find a prettier threshold. The high-information successor is a materially different delivery stack/environment (real WSLg/Xwayland or native non-X11 input path) and/or explicit CPU/power cost comparison of busy-wait versus a lower-overhead scheduler/pacing mechanism while keeping correctness fixed.
