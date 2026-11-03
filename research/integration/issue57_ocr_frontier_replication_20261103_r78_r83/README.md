# Current-main OCR guard replication r78–r83 — 2026-11-03

## Result

**BLOCK_GATE_FAIL.** Six additional fresh Calc runs completed on current main `8bb083ac3680715089a22bebbbc4198399758f4d`, in three preregistered pairs with B→A, A→B, B→A order. Five of six arms passed every functional gate. All three forced-OCR arms passed; two of three predicate-skip arms passed.

| Pair | Order | Forced OCR: calls / OCR ms / profile ms / task gate | Predicate skip: calls / OCR ms / profile ms / task gate |
|---|---|---|---|
| 1 | B→A | r78-b5: 17 / 1243.820 / 2823.420 / PASS | r79-a5: 7 / 525.720 / 2242.580 / PASS |
| 2 | A→B | r81-b6: 17 / 1233.700 / 2819.540 / PASS | r80-a6: 7 / 632.470 / 2968.290 / **FAIL** |
| 3 | B→A | r82-b7: 17 / 1397.570 / 3330.770 / PASS | r83-a7: 7 / 499.160 / 2221.900 / PASS |

r80-a6 is retained as a failed arm. The pre-close verifier reported `populated_cell_set_mismatch`; the later parent verifier returned `unknown` / `target_process_exit_required`. The close receipt shows the target required SIGTERM and did not prove natural exit, although input release was confirmed. A read-only XML inspection of the retained FODS showed A1=731 and A2=864, but that does not repair the independent verifier failure or establish a clean app exit. Cause remains undetermined; the arm is not eligible for an efficiency pass.

In the two pairs where **both** task gates passed, predicate skip used 10 fewer OCR calls, OCR elapsed was 57.7% and 64.3% lower, and profile elapsed was 20.6% and 33.3% lower. Pair 2 is fully reported above, including its profile time rising by 148.750 ms under skip, but cannot be counted as a passing performance pair. These descriptive readings do not override the block failure or support a general speed claim.

## Conditions and evidence

The preregistered task, main source, pinned Docker image/package versions, Calc profile, OCR parameters, per-container CPU/memory/PID limits, release and natural-exit gates, and analysis are recorded alongside all six arm directories. No models, providers, APIs, WSLc, MAP01, or Docker setting changes were used. No retries or post-hoc exclusions occurred. All containers exited and Docker is responsive; this run yielded no new evidence explaining prior Docker Desktop backend exits.

- [Preregistration](preregistration.md)
- [Source freeze](source-freeze.json)
- [Machine-readable arm and pair analysis](analysis.json)
- [SHA-256 manifest](SHA256SUMS.json)
- Earlier distinct current-main pair: [`r76/r77`](../issue57_postclose_ocr_pair_20261103_r76_r77/README.md)

This is still one fixed scripted Calc workload. It measures local OCR and compiled-profile time, not model/provider token efficiency, price, general reliability, other applications, WSLc, MAP01, or completion of Issue #57. Keep Issue #57 open.
