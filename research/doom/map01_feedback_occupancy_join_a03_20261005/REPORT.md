# Per-key admission identity reconstruction test — A03

Status: `HOLD_CANDIDATE_CONSTRUCTION_DEFECT`.

## H/T/D/C/U

- **H:** Per-key `input_admission` records cannot be safely assigned to aggregate `keys_held` receipts using only later timestamp and key membership, because the admission records lack program/step identity.
- **T:** Freeze and hash-check the retained 634-event v39 stream. For each of 39 admissions, enumerate every later `keys_held` row containing its key. Separately compare the admission and aggregate key sets within explicitly identified steps. Run a constructed overlapping-key sequence through a greedy-next-match rule and an independent auditor.
- **D:** PASS requires exact pinned inputs/counts, at least one multiply-matched admission, consistent per-step key sets (a weaker aggregate check), and an independently confirmed greedy misattribution example.
- **C:** An undocumented serial-order invariant or external runtime/source identity may permit stronger reconstruction; this test does not assume either.
- **U:** One offline trajectory and the tested join rule only. No physical keyboard occupancy, key-up timestamp, application effect, useful feedback, causal attribution, or live behavior is measured.

## Result

The first candidate invocation returned a nominal PASS with 634 events, 39 admissions and 28 aggregate receipts. It reported 6 unique, 33 ambiguous, and 0 unmatched admissions. However, it incorrectly expected aggregate key sets to be consistent and its constructed example did not actually establish misattribution. Those construction defects invalidate the frozen decision gate; this package is therefore HOLD, not a scientific PASS. Preserve the raw candidate output in `RESULT.json` as the first outcome.

The candidate ran once; the independent auditor was not run because the decision-gate construction was found invalid before audit. Three earlier invocations stopped before source read/output due root-path construction errors; one hash-check stop found a nonexistent README path. No source or historical result was changed. No live game/model/GUI/input or container operation occurred.

## Consequence

The candidate's 33 multiply matched admissions are suggestive but not independently audited here. Do not use this package as proof that reconstruction is impossible. Future instrumentation should carry a stable occurrence, program, step, key, and admission identity through the per-key request/ack and per-key up/release bracket. A02's exact observation/feedback event identity result is unaffected.
