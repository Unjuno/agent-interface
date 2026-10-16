# Bounded verifier wait

The partial-terminal live run needed ten caller-side effect queries after its one
safe submission. `effect_checkpoint_v3.py` moves that bounded polling inside the
verifier worker. The caller declares `wait_ms` and `poll_ms` in one durable query;
the result remains UNKNOWN or VERIFIED evidence with no input authority.

Two fresh Chromium sessions used the same seed, task, runtime candidate and
five-second delayed artifact. Both submitted once and independently saved the
exact value.

| Condition | Post-UNKNOWN durable calls | Time to VERIFIED | Total durable calls | Internal samples |
| --- | ---: | ---: | ---: | ---: |
| caller poll, 500 ms | 10 | 5,060.458 ms | 15 | 1 per call |
| verifier wait, 6,000/50 ms | 1 | 4,897.769 ms | 6 | 97 |

This reduces agent/runtime round trips by 90% in the fixed pair and reaches
VERIFIED about 163 ms earlier. It does not eliminate sampling, reduce model
tokens, or establish lower CPU/IO cost. The worker still checks the filesystem
97 times. It is a bounded long poll rather than an application event subscription.

The command is opt-in and accepts either an ordinary checkpoint or both bounded
wait fields. Fourteen service/journal controls reject negative, oversized,
partial, inconsistent and extra inputs before any GUI/model work. The journal
holds its existing single-writer lock for the long exchange, so this candidate
also does not establish useful concurrency for one cooperating caller.

Artifacts are in `results/effect-wait-ab-01/` and
`results/effect-wait-controls-01/`. `audit_effect_wait_v1.py` verifies pinned
sources, exact frames, one task Return per session, empty releases, checkpoint
counts and commands, saved bytes, independent scores and cleanup on Windows and
Linux.

The next fresh integration uses this wait after actual model decisions. Its
before-Return recovery path reduces post-decision effect calls from ten to one
and total durable calls from 17 to 8 while preserving independent success. See
`PARTIAL_TERMINAL_WAIT.md`. Cross-run latency remains confounded by model-time
variation.
