# Preserve possible effect when cancellation loses the execution receipt

Worker `01a0ff2c-34fb-73a0-b3aa-bdf13badf325`, FINAL-v5; parent #57.
Ordinary sequential kernel repair, with no formal allocation or native input.

## Problem and resulting behavior

After a successful `begin_execution`, the backend can fail before returning an
execution receipt. Cancelling with verified empty input then previously returned
`effect_occurred=False`, even though prior input could already have had an effect.
The retained inert backend demonstrates two histories: failure before incrementing
an in-memory application counter, and failure after incrementing it. Both expose
the same missing-receipt evidence to the kernel. Neutral release distinguishes
neither history and does not prove semantic abort.

The repair preserves possible occurrence when a request has begun but its
execution receipt is unavailable. This uses the existing boolean convention:
both `EffectOccurrence.POSSIBLE` and `OBSERVED` already map to true. Without an
accepted begin the flag stays false; a rejected begin creates no request; an
accepted execution receipt explicitly reporting `NONE` still maps to false.
Effect verification, release requirements, input admission and replay behavior
are unchanged. True is not proof of a task effect or permission to retry.

| Authored history | Expected possible-or-observed flag | Before | After |
|---|---|---|---|
| Cancel before begin | false | false | false |
| Accepted begin; unavailable receipt; inert effect not applied | true | false | true |
| Accepted begin; unavailable receipt; inert effect applied | true | false | true |
| Accepted explicit NONE receipt; cancel | false | false | false |
| Accepted explicit POSSIBLE receipt; cancel | true | true | true |
| Accepted explicit OBSERVED receipt; cancel | true | true | true |

## Verification and source custody

Initial exact Git source at `f1416985d4ff9ce5bbf9f0f4be1be3d0ee669549`:
original18 + eight construction regressions ran26 tests, with two expected failing
subtests in the missing-receipt test. The isolated candidate passed26/26 normally
and with Python `-O`. These are ordinary construction checks, not replicates of a
scientific allocation.

PR #6853 then merged its single-begin repair. This actual repair starts from
`cb13a10dce358649458f5aea00947b8aa43fc5b8` and preserves that guard. Test-first
current-main check: original21 + four focused regressions ran25 tests, with one
expected false-versus-true assertion failure. The repaired source passes25/25 normally and
with `-O`. The existing kernel workflow runs this same test module; no workflow
or automatic formal allocation is added.

Git staging normalized mixed checkout line endings. The actual canonical LF
staged kernel bytes were therefore materialized separately and also passed25/25
normally and with `-O`; [canonical checks and pins](CANONICAL_CHECK.json) bind
those executions to the staged source. The original checkout checks remain
retained. All runs used Windows CPython3.12.10, not a cross-platform backend.

Two six-history raw files retain the current-base before/after outcomes. A
separate JSON-only oracle imports neither producer nor kernel, reconstructs the
two missing-possible flags before repair and zero after, and detects six directed
corruptions: missing/duplicate case, false pending flag, invented verified effect,
false release and wrong command. Raw hashes are identical to the initial
construction counterparts because the single-begin guard does not change these
six histories; they are not pooled as new independent observations.

- [Exact source pins](SOURCE_PINS.json) and [initial pins](INITIAL_SOURCE_PINS.json)
- [Before raw](raw-before.jsonl) and [after raw](raw-after.jsonl)
- [Raw producer source](raw_producer.txt) and [inert construction fixture](construction_fixture.txt)
- [Actual commands, exits, clocks and source hashes](CHECKS.json)
- [Original red check](baseline-red-tests.stderr.log), [current-base red check](current-main-red-kernel-tests.stderr.log), [green](current-main-green-kernel-tests.stderr.log), [optimized green](current-main-optimized-kernel-tests.stderr.log)
- [Canonical green](canonical-normal.stderr.log) and [canonical optimized green](canonical-optimized.stderr.log)
- [Independent result](INDEPENDENT_CHECK.json), [verifier](verify.py) and [its exit receipt](VERIFY_RUN.json)
- [Public log redaction provenance](LOG_PROVENANCE.json) and [workflow inspection](WORKFLOW_INSPECTION.json)

Only private workspace prefixes are redacted from public tracebacks. Complete
original bytes remain in this worker's dedicated outputs. Source blob/hash
verification uses actual bytes; the original six source blobs were independently
reconstructed and matched Git object identities before execution.

Local entry points:

```sh
python -m unittest -v runtime.kernel.test_kernel
python -O -m unittest -v runtime.kernel.test_kernel
python runtime/results/kernel-cancel-effect-01a0ff2c/verify.py
```

The last command reads retained raw and prints a check without writing files or
executing the producer. The two `.txt` files preserve the actual initial producer
and its helper; they are not test discovery or auto-import entry points.

## Limits and integration

H: an accepted begin with no execution receipt must not erase possible effect.
T/D: the finite table and directed before/after regression controls above determine
this reporting property. C: begin alone emits no input, so the no-effect world is
still possible; the repair deliberately preserves uncertainty rather than proving
an effect. U: native OS/application cancellation, physical release, clock provenance,
thread safety, public MCP behavior, task success and speed are unmeasured.

This does not repair standalone cancellation-release freshness (#6864), execution
start/effect/lease timestamp questions (#5215), or any historical evidence.
The parent single-begin guard (#6852) remains intact. No shared container, WSLc,
GUI/input/GPU/model resource or main writing lock was acquired. Draft publication
and content consensus are separate from checked conditional main application.
