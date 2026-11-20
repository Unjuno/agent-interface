# Run record

- Classification: deterministic, read-only post hoc reconstruction of a retained live run; no new allocation.
- Run source commit: `b67fc4f33a28f9cea1c4c6cb2d95a470f6be53f3`.
- Current-main source comparison was pinned to `ff13baf57d5f1c12819151e668b92cb6db4a7c1c`; worktree started at `d3a51bc4c962b223d05280225042b96a033df8bf` before main advanced.
- Candidate command: `python3 -B research/doom/v39_invalidation_latency_59_p02_20261005/analyze.py --output /tmp/v39-invalidation-59-p02-replay-result-20261005.json`; final exit 0, source/frame/runtime identities verified.
- Independent auditor command: `python3 -B research/doom/v39_invalidation_latency_59_p02_20261005/audit.py --result /tmp/v39-invalidation-59-p02-replay-result-20261005.json --output /tmp/v39-invalidation-59-p02-replay-audit-20261005.json`; exit 0, 17/17 checks PASS.
- Replay result and audit are byte-identical to the retained `RESULT.json` and `AUDIT.json`; SHA-256 values are `9776174467c5513c345eac6b341b64e759b7ddc72f9dccb352515d0ad0da7340` and `2a5b42b3af8b527a7b826e3efe50c5fb111e0ff2a2c5e1bf1a5349766602d27a`.
- Earlier previews and two surfaced implementation/audit failures are preserved and explained in `HISTORY.md`.
- Exact source report, event log, fixture and reviewed PNGs are read with `git show`; no source files are materialized or changed by the scripts.
- No runtime, game, GUI, model or input was invoked. No container was used because this is a standard-library parser over retained Git blobs, not a new experiment.
- Scope exclusions: no causal enemy-damage attribution, no per-key release claim, no bounded recovery claim, no survival benefit, and no MAP01-clear claim.
