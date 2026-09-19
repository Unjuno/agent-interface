# Office X11 text pacing v1 — retained first comparison

**Result ID:** `office-x11-text-pacing-v1-20260916-01`  
**Source/plan freeze:** `c5a83daf3eb97b0cf8afc23f19f346ed20af2d85`  
**Dependency base:** `4e16d8aec4b8f13eaceaab46bf97763fdb44396a` (real Calc integration)

## Disposition

**PASS_MINIMUM_TESTED / RETAIN_1MS_CANDIDATE / DO_NOT_GENERALIZE**.

All six source-frozen arms completed in the preregistered order `0,12,2,8,1,4 ms`. Every arm preserved stale-observation zero-input refusal and verified empty terminal release. The independent XLSX scorer found:

| pacing | exact corpus | eligible | task elapsed |
|---:|---:|:---:|---:|
| 0 ms | 1/16 | NO | 1622.521 ms |
| 12 ms | 16/16 | YES | 3407.578 ms |
| 2 ms | 16/16 | YES | 1936.338 ms |
| 8 ms | 16/16 | YES | 2817.733 ms |
| 1 ms | 16/16 | YES | 1790.501 ms |
| 4 ms | 16/16 | YES | 2216.928 ms |

The minimum **tested** eligible pacing is therefore **1 ms/character**. No sub-1-ms threshold is inferred. On this one fixed workload, 1 ms reduced task execution by **1617.077 ms (47.46%)** versus the retained 12 ms policy while keeping exact durable workbook output.

## Negative control

0 ms is not merely slower/noisier; it is semantically wrong. Fifteen of sixteen strings mismatch despite executor transport success and verified release. Examples include `coffee→cofe`, `bookkeeper→bokeper`, `committee→comite`, and repeated-key strings collapsing heavily. This directly falsifies the policy `no pacing is sufficient` for this environment.

## Hard gates

- source readback: 8/8 local files matched GitHub blob IDs before first formal arm;
- stale observation: refused with `STALE_OBSERVATION`, backend emissions unchanged in every arm;
- executor transport: completed in every arm;
- terminal release: verified empty in every arm;
- semantic score: separate post-execution openpyxl process;
- formal order fixed before first arm;
- no model/provider/network call;
- no formal arm was rerun.

The outer container display appended `TERM environment variable not set` after individual arm commands; decision evidence comes from retained internal executor/scorer/aggregate receipts. This wrapper anomaly did not trigger reruns.

## H/T/D/C/U

**H:** the prior 12 ms Calc policy is conservative; a lower pacing can preserve exact strict-ASCII semantics while reducing avoidable local delay.  
**T:** one source-frozen six-arm comparison, fresh private Xvfb/Openbox/LibreOffice Calc session per arm, fixed 16-string repeated-character corpus, separate XLSX scorer.  
**D:** PASS for 1 ms as the minimum *tested* eligible value because 0 ms fails and 1/2/4/8/12 ms pass all correctness/release/stale gates.  
**C:** the threshold may depend on compositor/WM load, application, text input method, CPU scheduling, string distribution, locale, or real desktop delivery.  
**U:** one machine/container, Xvfb/Openbox, strict ASCII, Calc only, one session per arm, uncontrolled shared-host timing. The 47.5% number is fixture-local, not a general product speed claim.

## Successor

Retain **1 ms as a candidate**, not a universal default. The next discriminator should run 1 ms vs 12 ms on a second real application or a changed-host/load condition with the same exact-text + durable-effect scorer. A native backend should independently reproduce the pacing requirement rather than inherit it by assumption.
