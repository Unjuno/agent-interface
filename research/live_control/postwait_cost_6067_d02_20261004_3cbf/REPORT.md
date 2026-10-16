# D02 actual result: HOLD_NOT_REPRODUCED

Issue #6067. Source c3fe1cd39c60a50ec494e4b280d3a0ccc0b2b3f1; public freeze 555e372c4a1df0d11be6fc1af58b7f770f8bed95, before acquisition. Allocation POSTWAIT-COST-6067-D02-20261004-3CBF is consumed: native1, saved diagnostic auditor1, retries0; official114 science0. Do not rerun.

## Progress and question

Fresh main/docs/issues/PR/branch intake found the full roadmap still incomplete. A03 evidence was integrated via PR7152, but its first formal exposure STOP did not establish phase efficacy. D02 tests a different bounded hypothesis: whether the synchronous resource snapshot immediately after draw-wait adds at least0.5ms delay consistently across six balanced serial pulse pairs. The prospective H/T/D/C/U and immutable protocol are in README.md, plan.json and FREEZE.json. No peer paths or allocations were modified.

## Actual execution

Native UTC 2026-10-03T17:53:03.193065105Z–17:53:27.407820032Z, producerexit0: COMPLETE_DIAGNOSTIC,16cells,128actual captures,98source events,196source waits,599snapshots. Saved-only auditor UTC17:57:28.813470154Z–17:57:29.118889116Z, exit0: PASS_SAVED_DIAGNOSTIC_AUDIT. This is diagnostic integrity, not scientific efficacy PASS.

Frozen support requires pooled median(full−minimal)>=500000ns AND at least5of6 paired median reductions>=500000ns. Pooled678690.5ns passes its component; only4of6 pairs pass, so the primary result is HOLD_NOT_REPRODUCED.

| Pair | Reduction ns | >=500000ns |
| --- | ---: | --- |
| 0 | 433795 | no |
| 1 | 428358.5 | no |
| 2 | 591648 | yes |
| 3 | 1078588.5 | yes |
| 4 | 930608.5 | yes |
| 5 | 1132068 | yes |

Pulse-only48events per arm: median delay full733066ns, minimal54375.5ns; median trial thread CPU704604ns versus5666ns. Timing failures are retained outcomes, not censored cells. Correct posthoc descriptors are posthoc/DESCRIPTIVE_V2.json. The first prefix-based descriptor erroneously included persistent controls; DESCRIPTIVE.json is preserved unchanged and INVALID_V1.md explicitly excludes it. Frozen primary producer/auditor arithmetic was unaffected.

## Remaining failure boundary

In p3_minimal event1, draw-post snapshot is null yet source coarse sleep overshot51.179783ms, draw-wait returned36.179783ms late, and exposure was1.590675ms (<5ms). Observer sleep overshot58.180324ms and capture started44.093787ms late. Return-to-paint was only71.167us. Decoded cue1 is temporally possible diagnostic data, but extraction ends245.668us after clear starts: not stable-interval scientific qualification. Details: posthoc/P3_MINIMAL_TAIL.json.

Removing this telemetry did not ensure eligibility in the observed profile. Why coarse sleep overshot remains unresolved. Broader source pre→clear.pre and observer pre/post leaf counters stay2/3799us; whole native leaf rises0→3 throttles and0→7370us. Neither ancestor/host contention absence nor timer/VM root cause follows. Serial order/carryover and shared physical-host confounds remain. No A03 causal attribution,114phase benefit, model/task efficacy, safety, rare-tail guarantee or hard-real-time conclusion.

## Custody and checks

staging/ receipts retain32source files unchanged before/after native and saved audit; all290native files match original/export/host/delivered, and all10audit files match four copies. Raw files remain native-raw/ and saved-audit/. Runtime inspections retain CPU1,512MiB,swap0,PIDs64,nonroot501:501,networknone,read-only mounts/root,capdropALL,no-new-privileges, no OOM/restart. Xvfb lifecycle is the frozen owned-server planned-SIGTERM contract, not a rewrite of historical child-exit rules.

Nine retained actual-cell semantic corruption controls were rejected; they do not establish full wrapper/custody mutation coverage. Pre-native method tests43PASS. Source review is separate from saved diagnostic audit; result review scope is recorded in RESULT_REVIEW.md when available. No broad repository/native replay test is authorized.

## Delivery boundary

GitHub content creation returned secondary-limit403 before launch. Public source/freeze readback already succeeded; the failed comment was not published. No identical API write retry, alternate API writer or new wrapper Issue. publication/secondary-rate-limit.json retains the first error. D02 PR/main integration remains pending; source/results are preserved on its existing additive branch. A future rate-state change permits reviewed PR plus applicable CI, not a rerun of this consumed block.
