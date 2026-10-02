# Issue #5771 T1 allocation-03 result

**Disposition: `PASS_METHOD_SCOPED`.** This is a deterministic synthetic method result only.

## Frozen question

Can a finite feasibility ledger distinguish observation alias from missing response, authority restriction, and a deadline miss? Allocation-03 is frozen in [FREEZE.json](FREEZE.json), dispatched once from commit `f370c39bfe3042c5c2c77313f897c913137aebc5` under [GitHub Actions run 36818517390](https://github.com/Unjuno/agent-interface/actions/runs/36818517390).

The candidate and independent auditor each ran exactly once, in separate `linux/amd64` Docker containers using `python:3.12.14-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`. Both exited 0; the audit returned `PASS_METHOD_SCOPED`, 7 interventions, 5 offered disturbances per intervention, zero errors. The raw output is 9,231 bytes with SHA-256 `e6e35effe4fe964182cd6004d40f6d52b3759fbac10585ea6d6b33df499d0a4d`. Candidate, auditor, raw, server/image identities, container inspections, invocation receipts, and checksums are retained beside this report.

Docker inspection confirms `network=none`, read-only root, all capabilities dropped, `no-new-privileges`, PID limit 32, 128 MiB memory, 1 CPU, and no OOM for both containers. The image digest/platform match the freeze.

## Observed finite distinctions

- Baseline and verifier-only retain the focus-loss/target-mutation observation alias; the extra verifier changes no observation or response edge.
- Observation refinement separates that pair, but the worker-exit disturbance remains `NO_RESPONSE`.
- Adding `restore-session` covers worker-exit, but the original observation alias remains.
- Combining observation refinement and the added response removes both of those gaps; the separate backend restart remains `AUTHORITY_GAP` because authority is false.
- The slow response remains `DEADLINE_GAP` when its authored latency exceeds the fixed deadline.

The test suite also passed 2/2 before dispatch, including a mutation control that removes an offered disturbance row and verifies auditor rejection. Allocation-01 (`STOP_BEFORE_CANDIDATE`) and allocation-02 (`STOP_RAW_IDENTITY_GATE`) remain separate immutable failures; allocation-03 did not rerun either.

## Interpretation and limits

This result shows that the finite ledger implementation distinguishes the authored cases and that the independent raw reconstruction agrees with the candidate. The state machine, observation map, authority labels, required responses, and latencies are all hand-authored. It does not show that these are complete GUI disturbance classes, that any real interface lacks or has a recovery capability, or that extra verification is generally useless. It establishes no production reliability, task safety, model behavior, causal GUI effect, or quantitative Ashby law. The prediction remains untested against a resettable live GUI task family.

See [Issue #5771](https://github.com/Unjuno/agent-interface/issues/5771) and [allocation freeze](FREEZE.json).
