# Frozen T0 result — Issue #6278

## Disposition

`PASS_METHOD_SCOPED` for the narrow exact-effect/temporal eligibility fixture only. This is **not** an optimization result, topology comparison, evidence of a buffering advantage, or GUI result. The allocation is consumed: one candidate invocation, one independent audit invocation, zero retries.

## Execution

- Source main: `1e16d213e93aaefb4420c1a41f7253220aa553bc`
- Frozen manifest: [`FREEZE.json`](FREEZE.json)
- Container: `python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b`; network disabled, read-only root and source mount.
- Candidate command: frozen command 1 in `FREEZE.json`; exit 0; invoked once.
- Auditor command: frozen command 2 in `FREEZE.json`; exit 0; invoked once.
- Candidate raw rows: 8; independent expected rows: 8; discrepancies: 0.
- Audit disposition: `PASS_METHOD_SCOPED`.
- Raw SHA-256: `c76437098e2d39710bccd1eb10137e789dab9b2482ee1b531a2688740dd76f42`
- Audit SHA-256: `5503852df141c07ced3303829cfaad069765cdd2fd023231abd3b40c731cd35f`

The first post-allocation construction-suite invocation from the repository root failed at test discovery (`ModuleNotFoundError: candidate`) because this standalone test expects its package directory on `sys.path`. It did not invoke the frozen candidate or auditor. Running the same construction suite from the package directory passed 6/6; no source change or formal retry was made.

## What was discriminated

- Exact, authorized, on-time nominal tasks were counted.
- Shared dependency loss caused both routes that relied on that dependency to abstain.
- Reconfiguration plus readiness plus effect latency beyond the task deadline did not count as buffering.
- Partial effects and unauthorized tasks were not counted as completed obligations.
- Four corruptions (fabricated route, late completion relabeled as success, missing row, duplicate row) were rejected by construction tests.

## Scope and next gate

The candidate uses a deterministic greedy choice; the auditor is a separately implemented recomputation, **not** an exhaustive assignment oracle. The fixture does not optimize equal-budget portfolios across identical-copy, disjoint-specialist, partial-overlap, and universal-fallback design classes. It also does not prove any edge from a real application trace. Therefore Issue #6278's portfolio H and T1 remain open; this package only validates a narrow eligibility boundary that those later stages must preserve. No held-out task family, application, GUI, model, or human run was performed.

## Post-run overlap check

After the frozen run, current `main` added the completed #6184/#6181 passive-sensor-cover enumeration. That experiment exhaustively selects observation-channel subsets and checks producer dropout; it does not compare task-route portfolios or score completion before per-obligation deadlines. This package does not duplicate its subset-selection result. It is still only a prerequisite/boundary result for #6278, not evidence for partial-overlap advantage. The frozen run remains tied to source main `1e16d213e93aaefb4420c1a41f7253220aa553bc`; main fast-forwards to `389b109629ca0c8baf7a9daf725eded76c358162` were outside the package path and did not change the frozen input.
