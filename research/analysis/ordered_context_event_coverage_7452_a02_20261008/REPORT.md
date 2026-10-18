# Successor #7452 A02 — equal-denominator result

## Verdict

`PASS_METHOD_SCOPED` for the frozen 64-obligation synthetic universe. A02 corrects A01's unequal-denominator comparison; A01's report and raw audit remain unchanged. This establishes neither real-GUI performance nor a general ordered-t-way efficiency claim.

## Formal run

- Design main SHA: `2f36f501f11931e052dbc3fb0000a9200bff7f50`.
- Frozen source commit: `2e4eae4ba2`.
- Environment: host Python 3.12.13, CPU-only. No container, model, GUI, or network was used; this is not container evidence.
- Pre-formal construction test: 1/1 passed; Python compilation passed.
- Candidate invoked once, exit 0; candidate SHA-256 `01ee3aa37706ba20c6e76c60fd79b53e476d4ab87e935f6541fa776d35d7a2f9`.
- Independent auditor invoked once, exit 0; `AUDIT.json` reports `PASS`, errors `[]`; retries 0.

## Results

- Mixed and exhaustive suites independently reconstruct to the same 64 `(context-pair assignment, ordered event pair)` obligations.
- Mixed: 4 reset-bounded episodes, 32 rows. Exhaustive comparator: 64 reset-bounded two-row episodes, 128 rows. This is a like-for-like finite workload comparison: mixed uses one quarter the rows and one sixteenth the episodes for this enumerated universe.
- Every mixed episode covers all 16 ordered event pairs locally. No cross-reset pair is credited.
- Joint context-plus-order mutant gate activates only in mixed and exhaustive; context-only and order-only controls activate in their scoped suites and mixed/exhaustive. These control entries measure seeded gate activation, not downstream effects.
- The separately simulated correct negative-control policy produced no ACT admission while authority was revoked.
- Four hostile audit-input mutations were each rejected: dropped episode, unknown event value, fabricated cross-reset credit, and collapsed context strata.

## Limits

The sequences, transition system, mutants, and denominator are authored and exhaustive only within this tiny model. No observed GUI history, real fault corpus, human usability, safety effect, or production test cost was measured. The result does not prove broader NIST OCC conformance or transfer beyond this explicit row/episode mapping.

See [FREEZE.json](FREEZE.json), [CANDIDATE.json](CANDIDATE.json), and [AUDIT.json](AUDIT.json) for retained source binding and outputs.
