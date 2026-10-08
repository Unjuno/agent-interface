# Registered recovery comparison — pair 3 complete

Six of eight registered episodes have executed. Pair 3 tests OpenTTD depth 1
in B then A order; both have completed. The seed field 203 is a pair label, not a
game RNG override. The canonical save fixes the starting world.

B used the frozen pending-clock helper for one read in one model orchestration
call. Its complete assembled history and original image were reviewed before
opening the road toolbar. The road program completed with verified input release.
Independent scoring confirmed the three owned, connected target road tiles,
clear forbidden row, and unchanged surrounding road ownership.

| Measurement | A | B |
| --- | ---: | ---: |
| Recovery socket reads / reported outer calls | 1 / 1 | 1 / 1 |
| Total socket exchanges | 10 | 10 |
| Unique raw events / exact decoded frames | 47 / 7 | 47 / 7 |
| Initial capture to final program terminal | 51.610374 s | 51.688963 s |
| Initial capture to independent evaluation | 64.667922 s | 317.616787 s |

A's full recovery history, open/build views, and original images were reviewed
without visible truncation; its independent guard score and cleanup also passed.
Initial PNG bytes, explicit task steps, and runtime manifests match across arms.
Later image bytes differ as the running simulation advances. Both arms need one
recovery call/read: no call or socket-read reduction at depth 1. B minus A full
elapsed time is +252.948865 s, retaining B's presentation interruption.

The build result exceeded available model context. After compaction, an attempted
full saved-result read was also truncated. The saved terminal and original
007.png were then inspected separately before finish. No build input was retried.
This is a retained presentation failure, not a clean full-history presentation
episode. Reversible duplicate removal does not bound unique-event output or
remaining model context; do not claim that it solves output overflow.

The full elapsed time includes this interruption and result inspection. Runtime
timestamps are not model receipt timestamps. Exact model identity/configuration,
actual input tokens and cost are unavailable, so model-performance qualification
fails. The elapsed difference is descriptive, not a causal helper effect.

Evidence: `results/recovery-pair3-01/B/`; reproducible audit:
`python3 research/live_control/audit_recovery_pair3_b_v1.py` in the Linux research
environment. The audit verifies pinned runner/plan/runtime sources, every received
slice against raw event positions with full coverage, own-clock identity, stale
program suppression, view reversibility, exact PNG/decoded-frame equality,
independent guard scoring, and owned-process cleanup with unchanged canonical save.
The audit cannot establish model receipt or visibility from runtime logs.

The paired audit is `python3 research/live_control/audit_recovery_pair3_v1.py`;
outputs are `pair-audit.json` and each arm's `paired-audit.json`. The earlier B-only
audit and presentation note are retained as historical artifacts.

Next: execute pair 4 at OpenTTD depth 3, A then B, once each. Keep both pair 3 results.
Investigate bounded, resumable presentation separately after the frozen comparison;
do not silently change the display contract for one arm to erase this failure.
