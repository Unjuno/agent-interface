# Incomplete release publication custody A01

## Question and frozen decision

Issue #59 asks the current control path to retain each per-key release receipt when its sink fails. The existing A01 covered failure while publishing a completed batch. This construction experiment isolates a different path: a step fails after some keys were released, then the backend tries to publish the remaining receipts as incomplete telemetry and that sink call itself fails.

The frozen hypothesis was that both current `main` and PR #7635's candidate would lose structured per-position custody in this path. The minimum test used three residual rows and injected a single sink error at position 1, in two externally controlled modes: fail before accepting the row, and accept the row then raise. The decision required the original step exception to carry `confirmed`, `delivery_unknown`, and `not_attempted` positions in both modes without retrying position 1.

A pre-freeze diagnostic at position 0 is also retained separately under `raw/preflight_position0/`. It motivated the middle-position frozen case but is not counted as the A01 candidate run and has no independent audit.

## Executed result

The candidate ran once against each of the two frozen backend snapshots, with one attempt per acceptance mode and no retry. In all four cases the sink attempt sequence was positions `[0, 1]`; position 0 was accepted; position 2 was never attempted. Position 1 was absent from delivered rows in the fail-before-accept case and present in the accept-then-raise case. In both cases the original `RuntimeError("original step failure")` had no structured `release_batch_publication` metadata. Its only note was `incomplete release telemetry publication failed: OSError`, and the residual buffer was then cleared.

The independent raw-only audit reconstructed all four cases and returned `FAIL_INCOMPLETE_PUBLICATION_CUSTODY` with no audit errors. This confirms the stated construction hypothesis for both frozen source versions. PR #7635's exact ExecutorV13 consumer places a terminal `release_batch_publication` field only when that structured attribute exists, so the observed missing attribute means this failure path cannot populate that terminal field. This last sentence is a source-path implication; the experiment did not execute a live ExecutorV13 or game.

## Source and environment

`FREEZE.json` binds the inputs to `main` `d6a3fe646d6a8ea92a8688a1f7c54b89261f56f6` and PR #7635 head `bf57eb60009867bfa36243a9b48e37bd576682c7`. Exact backend and ExecutorV13 source snapshots are retained in `source_snapshots/`; the backend SHA-256 values are `a9e109f07dbfdefbf33e87840528c4e24195b2d435782d92f0880049721d0b7d` and `ee4872770ad4f3009883e6472e59c6584d3f1b3bed145b9bee7cefc8ad13e834` respectively.

The host was macOS 27 ARM64 with Python 3.12.13. OrbStack reported a running engine, but its local image listing failed with an unsupported containerd blob operation; no image was pulled and no container was launched. This deterministic host-CPU construction check therefore ran without a container. It used no network in the probe and exercised no game, model, GUI, native input, or physical release.

## Reproduction and retained evidence

From this directory:

```sh
python -B probe.py > raw/RAW.json
python -B audit.py > raw/AUDIT.stdout.json
```

The retained `raw/RAW.json` is the one candidate output. `raw/AUDIT.json` and `raw/AUDIT.stdout.json` are the one independent audit result. `SHA256SUMS` binds the freeze, source snapshots, runner, auditor, and raw outputs. This establishes only a deterministic construction/evidence-custody defect in incomplete telemetry publication. It does not establish that physical release failed or characterize production sink persistence semantics.

On 2026-10-05, the auditor was replayed against the preserved raw solely to check package integrity after this report's follow-up-status correction. Its stdout exactly matched the original saved audit; this extra invocation is separately retained as `POSTCHECK.json` and `raw/POSTCHECK_AUDIT_REPLAY.stdout.json` and is not counted as the frozen A01 audit.

## Follow-up status

After A01, PR #7635 advanced from the frozen pre-fix head `bf57eb60009867bfa36243a9b48e37bd576682c7` to `ddff6ebf8cea186accaae5dca98750ac16bb6a4b`. Its updated source now maintains a per-position ledger during incomplete publication and its tests cover a position-1 failure in both sink-acceptance modes, including propagation to ExecutorV13 terminal. This supersedes the defect on that PR branch; PR #7635 remains a draft source-repair path at the time of this note. A01 remains evidence of the defect on its frozen inputs, and does not imply the repair is merged to main or that live readiness is established.
