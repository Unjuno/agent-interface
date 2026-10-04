# A05 — exact typing at both V39 pair-identity rows

## H / T / D / C / U

- **H:** A03 compares down/up row identity tuples with ordinary Python
  equality, then validates only the down row's `step` type. An exactly equal
  float in the up row can therefore join to an integer down step. The same
  equality rule can alias integer `1` and boolean `True` across rows. A
  successor that validates identity field types on both rows before equality
  should reject these cases while preserving the retained pair.
- **T:** Read the retained A03 bytes and apply in-memory mutations only. Check
  one up-row int-to-equal-float replacement and an int-1/bool-True pair. Invoke
  only the pure reconstruction functions; do not run A03's consumed candidate
  invocation or write into A03's result directory. Exercise fixed successor
  functions and independent reconstruction against baseline and mutations.
- **D:** A03 acceptance of the equal-float up step and the paired boolean alias
  establishes the counterexamples. A05 passes only if the exact baseline joins
  and both corrected implementations reject each alias in either row.
- **C:** This is an offline identity-boundary check. It does not validate
  physical occupancy, application effect, useful feedback, threat response,
  recovery, matched performance, or MAP01 progress.
- **U:** One retained fake-display pair; no live GUI, game, model, or OS input.
  Other identity fields and consumer contracts remain outside this narrow test.

## Provenance and run boundary

Input and source identities are recorded in `FREEZE.json`. A03 source, freeze,
input, and result files remain unchanged. Test and independent audit outputs
are stored under `results/a05/`.
