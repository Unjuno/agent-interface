# V39 per-key measurement consumer A01

This offline integration applies a strict consumer to the exact two event rows
retained by `map01_v39_perkey_bridge_a01` A01. The source stream reports an
`input_admission` and a separate `input_release_measurement`; it does not emit
the batch-level `input_release_transition` required by the older direct-retained
analyzer. This package consumes the V12 measurement schema as such and does not
rename it into an authority-bearing release transition.

## Retained input and A01 STOP

The raw pair contains down-state bracket [87811364890958, 87811364895916] ns
and up-state bracket [87811364946333, 87811364949416] ns. Their arithmetic
gap is 50,417–58,458 ns. The sole candidate invocation stopped on a frozen
input-hash mismatch before emitting a candidate. The raw values remain intact;
no candidate/audit comparison was completed. See DISPOSITION.md and results/a01/.

No consumer PASS is claimed. These fake-display values do not establish exact
physical key occupancy, game consumption, useful feedback, threat response,
recovery, latency benefit or MAP01 progress.

## H / T / D / C / U

- **H:** The retained V12 down/up rows can be consumed into one conservative
  sample-bracketed duration interval while preserving owner, intent, key,
  actuation, program and step identity and explicitly denying authority/effect.
- **T:** Replay the frozen two-row bridge bytes once through `candidate.py`;
  independently derive expected output from the raw rows; reject identity,
  interval, release-status, type and authority mutations.
- **D:** `PASS_MEASUREMENT_CONSUMER_SCOPED` only if the raw hash matches, exactly
  one confirmed down/up pair joins, the source bracket matches each adapter
  edge, all interval/type/order gates hold, and the independent audit finds no
  mismatch.
- **C:** The intervals are from a fake display and are nested measurements,
  not a game-level or physical-effect receipt. A sample bracket bounds a
  transition only within the source's reported measurement contract.
- **U:** One retained F8 pair. No live X server, OS input, application, model,
  recovery, matched condition or product-level claim is measured.

## Reproduction

A01 was frozen as one-shot and its output directory was claimed by the retained
STOP. Do not rerun it. Its candidate, freeze, input, error and disposition are
preserved for provenance; a corrected attempt requires a new run ID and path.
