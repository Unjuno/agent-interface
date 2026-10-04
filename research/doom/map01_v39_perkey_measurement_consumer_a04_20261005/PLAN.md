# A04 — exact owner-interval typing follow-up

## H / T / D / C / U

- **H:** A03's candidate and independent raw auditor compare owner bracket
  intervals to adapter intervals using Python structural equality. Because
  `1.0 == 1` and `True == 1`, a bracket endpoint with the wrong JSON type can
  be accepted. An exact two-integer interval check at both consumers should
  reject these aliases while retaining the exact source pair.
- **T:** Use the retained A03 input bytes as immutable input. First make an
  in-memory mutation at the down bracket and then at the up bracket, replacing
  one integer endpoint with an exactly equal float. Invoke only the pure
  reconstruction functions, without running A03's consumed candidate,
  regenerating its freeze, or writing to its result directory. Then exercise
  the same cases against this versioned successor candidate and an independently
  implemented auditor, with boolean aliases and malformed/mismatching controls.
- **D:** The original A03 candidate and auditor accepting either float mutation
  establishes the counterexample. A04 passes only when the baseline raw pair is
  accepted and both corrected implementations reject every wrong-type and
  malformed interval while agreeing on the exact baseline brackets.
- **C:** This is an offline source-contract boundary. It does not validate
  physical key occupancy, application effect, useful feedback, threat response,
  recovery, matched performance, or MAP01 progress.
- **U:** One retained fake-display pair; no fresh allocation, GUI, game, model,
  or OS input. General consumer correctness beyond the tested interval join is
  not established by this narrow successor.

## Provenance and run boundary

Input is read from the A03 package at
`../map01_v39_perkey_measurement_consumer_a03_20261005/INPUT_EVENTS.jsonl`;
its bytes and A03 FREEZE remain unchanged. A03's previously consumed formal
candidate invocation and its outputs are not rerun or regenerated. A04 calls
only the focused pure functions under test. The exact commands and output are
retained under `results/a04/`.
