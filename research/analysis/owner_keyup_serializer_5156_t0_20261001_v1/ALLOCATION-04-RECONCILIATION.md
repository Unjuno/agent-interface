# Allocation 04 cross-record reconciliation (append-only)

Date of reconciliation: 2026-10-01. This note supplements, and does not rewrite, the Allocation 04 records merged through PRs #5581 and #5582.

## Evidence now on main

All of the following artifacts name the same formal allocation, `MAP01-OWNER-KEYUP-BRACKET-5156-20260930-04`, and the 2026-09-30 16:00–16:15 UTC window:

1. PR #5582 retained `results/formal-01/STOP.json`: a Docker command failed at the image ENTRYPOINT before Xlib/Xvfb/input (exit 2).
2. PR #5581 retained `results/formal-02/STOP.json`: another recorded command failed before the runner/Xvfb/input (Python parsed the supplied shell path; exit 1).
3. PR #5581 also retained `results/allocation-04-fail/raw.jsonl`, `runner.stderr.txt`, `xvfb.log`, and `RESULT.md`: the fixture recorded single-key, two-key, and partial-cancel admissions/terminal states, then the runner exited 1 at joined-release serialization with `TypeError: dict() got multiple values for keyword argument 'event'`. The raw stream ends with `runner_failure`; no joined release rows, runner-completion receipt, or formal independent audit were produced.

The first two per-invocation STOP records and the later fixture raw are mutually incompatible as a single invocation history. They are separate artifacts from parallel work, all carrying the same allocation identifier. The repo does not provide a unique invocation nonce that can reconcile them. Therefore one-shot/exclusive accounting for Allocation 04 cannot be verified; do not describe Allocation 04 as one clean formal attempt or infer that the input sequence was never executed.

## Correct allocation-level disposition

`STOP_ALLOCATION04_MULTIPLE_OR_INCONSISTENT_INVOCATION_RECORDS`

The fixture raw provides partial runner-authored state observations, but the central release-bracket rows were not serialized and no independent audit ran. The key-up timing hypothesis has **no formal verdict**: neither scoped PASS nor semantic FAIL is supported. Preserve every predecessor artifact unchanged.

## Follow-up boundary

The host-only serializer T0 at `research/analysis/owner_keyup_serializer_5156_t0_20261001_v1/` is a separate construction result (`PASS_SERIALIZER_CONSTRUCTION_ONLY`). It reproduces and fixes the duplicate-event serializer defect on synthetic rows; it does not re-run or audit Allocation 04.

A new X11 fixture requires a fresh allocation with an explicit exclusive coordinator assignment, refreshed main/source/image hashes, a corrected runner, and one uniquely tagged invocation followed by one raw-only audit only if the runner exits 0. Existing queued requests overlap; this note does not grant a Docker/OrbStack lease or authorize another formal run.
