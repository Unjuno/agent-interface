# A06 result: strict audit of the saved A05 result

## Result

`PASS_SAVED_RESULT_AUDIT_SCOPED`. The final corrected auditor independently reconstructed the complete saved A05 output from the raw event stream, verified all five copied A05 inputs against the hash manifests, confirmed frozen source provenance, and rejected all 15 result-only mutation controls. A05 was not edited and its candidate was not rerun.

The reconstruction found 39 per-key admission rows: 38 associated with exactly one later aggregate `keys_held` receipt under the preceding active hold-step interpretation, one cancelled `cover-4` step-10 Down admission without a same-step receipt, and no ambiguous associations. For the 38 associations, aggregate acknowledgement gaps were 8.853053–38.471932 ms (median 12.770812 ms). The aggregate receipt does not provide separate per-key acknowledgement or release evidence.

## Provenance and execution

- Raw source: commit `c99d93a2c81945f0946173e48247bdd49e32a02a`, `research/doom/results/v39-control-telemetry-gap-audit-20261004/events.jsonl`, 634 rows, SHA-256 `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.
- A05: PR #7692 head `0cc79dc4614b97751949960842013bd954c99dd7`; five byte-for-byte copied inputs are under `input_a05/` and cross-checked by the frozen manifests.
- Final run: WSLc 3.0.1.0, local pinned Python 3.12 slim image digest `sha256:414a398990af718f018ff9c23cea0e7489b7986eb54f2b1d7cc874c99ebc7364`, network `none`, CPU request 1, memory request 512 MiB. WSLc reported missing kernel swap/cgroup accounting, so memory enforcement is not claimed. CPU-only audit; no GPU allocation or candidate/live game/model/GUI/input run.
- Final independent output and container log/inspect are in `formal_02/`. The planned one auditor invocation was exceeded: a missing `git` executable caused one stopped attempt; a later review found the first passing auditor's input-manifest check was vacuous. That output is retained as `formal_01/AUDIT_INITIAL_SUPERSEDED.json`; the corrected auditor and final run are retained separately. `RUN.json` records every deviation and attempt.

## Interpretation and limits

This verifies the integrity of one saved posthoc result under a reconstructed same-step association rule. It does not turn that inferred association into a runtime-authored foreign key, prove per-key key-up or physical keyboard release, measure independently useful positive feedback or recovery benefit, provide a matched comparison, or demonstrate MAP01 completion. Issue #59 remains open and the next research gate is still a bounded corrected threat-exposure test once its live allocation prerequisites and ownership permit it.