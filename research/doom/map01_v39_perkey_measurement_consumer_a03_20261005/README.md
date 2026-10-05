# V39 per-key measurement consumer A03

This fresh successor changes the source-binding method after A01 and A02 each
stopped before result generation because of hand-transcribed SHA-256 literals.
Both STOPs remain preserved in their own paths. A03 generates the digest and
Git blob identity directly from the checked-out source and has the candidate
and independent auditor read the single generated freeze record.

The source stream has one input_admission and one separate
input_release_measurement. The consumer preserves that distinction instead
of relabeling the measurement as the older batch-level
input_release_transition.

## A03 result

The machine-generated freeze resolves input Git blob
eacb735634d6c6761ba7fa39448e6d7d43e342d5 and SHA-256
ad0b1c29da4b626e9be27e8716cdabfbb25ac49dcf0abd4bda4bd2f7a9f84e4e.
The one candidate run and independent audit pass. The 11 regression and
mutation tests pass in normal and optimized Python; source compilation passes.

The single retained pair yields a conservative sample-bracketed key-state
duration of 50,417–58,458 ns (50.417–58.458 µs). This derives from fake-display
state samples and is not an exact physical/game occupancy measurement. Neither
application consumption nor useful feedback was observed.

## H / T / D / C / U

- **H:** A generated freeze and strict consumer can convert the retained V12
  down/up measurement pair into a conservative per-key sample-bracket without
  granting authority or claiming application effect.
- **T:** One offline replay of the exact pinned two-row fake-display input,
  machine-generated freeze, raw-only audit, and ten mutation controls.
- **D:** PASS only if the generated source hashes and blob binding verify,
  exactly one confirmed pair joins with ordered brackets, candidate output
  matches independent reconstruction, and mutations are rejected.
- **C:** The stream was produced by a fake-display harness; its intervals are
  not exact physical or game-level key occupancy.
- **U:** One F8 pair; no live GUI, game, model, useful feedback, threat
  response, recovery, matched condition, or MAP01 progress.

## Reproduction

The recorded run used the base commit in FREEZE.json and the generated
source/input hashes listed there. Its candidate invocation is consumed; do
not rerun it or regenerate FREEZE.json in this result directory. For a fresh
reproduction, use a separate temporary copy at the exact pinned base commit,
generate a new freeze there, and compare its input/source identities before
running. The retained audit and normal/optimized tests can be rerun read-only.
A01/A02 failures remain preserved historical outcomes.

## Checksum integrity follow-up

The initial committed checksum list named two ignored test-log paths that were
absent from the PR tree. The original FREEZE, candidate, audit, RESULT, AUDIT,
and exit-status artifacts remain unchanged. This follow-up removes the missing
log references, records fresh normal and optimized regression transcripts as
`.txt` files, and adds a separate regression that checks all checksum paths
resolve. Only the 11-test regression suite was rerun; candidate and independent
audit invocations were not repeated.
