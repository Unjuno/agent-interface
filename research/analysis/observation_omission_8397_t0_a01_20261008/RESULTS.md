# Results — Issue #8397 T0 A01

**Disposition: `PASS_METHOD_SCOPED` (deterministic synthetic contract only).**
The candidate and independent raw-only auditor each ran exactly once after the
source/fixture freeze; both exited 0. The auditor reconstructed all five
scenarios and reported zero mismatches. The seven-test construction suite had
passed before freeze; its five adversarial mutation controls were all rejected.

| Scenario / arm | Visible events | Model-facing bytes | Exact effect | Safe stop | Regret vs baseline |
|---|---:|---:|---|---|---|
| Before sensitive decision — baseline | 3 | 41 | `target_saved` | no | no |
| Before sensitive decision — omit `[0,2)` | 1 | 17 | `target_saved` | no | no |
| Crosses relevant transition — baseline | 3 | 46 | `target_saved` | no | no |
| Crosses relevant transition — omit `[1,3)` | 2 | 27 | `target_missed` | no | yes |
| After completion — baseline | 1 | 16 | `task_complete` | no | no |
| After completion — omit `[3,6)` | 1 | 16 | `task_complete` | no | no |
| Captured but undelivered — baseline | 1 | 9 | `target_missed` | no | no |
| Captured but undelivered — omit `[0,3)` | 0 | 0 | `target_missed` | no | no |
| Mandatory safety — baseline | 3 | 31 | `safe_stop` | yes | no |
| Mandatory safety — omit optional `[1,4)` | 1 | 7 | `safe_stop` | yes | no |

The pre-decision fixture removes two visible events and 24 bytes (58.5% of
baseline model-facing bytes) while preserving its authored exact effect. The
transition-crossing fixture removes one event and 19 bytes but loses its
authored exact effect. Post-completion capture is invisible and costs zero in
both arms. Capture without delivery is not model visibility and cannot satisfy
the required cue. The mandatory safety event remains visible and stops in the
arm whose omission interval overlaps it.

The `captured_but_undelivered` baseline is already an authored failure, so this
fixture makes no comparison or causal claim about the omission intervention;
it tests visibility/accounting only. In this deterministic packet, one visible
event is counted as one model-facing observation call. Byte counts are the
fixture's declared payload lengths, not measured tokens or network bytes.

## Interpretation and limits

The method contract distinguishes a cost-saving insensitive interval, a
transition-sensitive interval, post-completion capture, delivery failure, and
mandatory safety monitoring. This is a self-authored finite fixture with
deterministic effects. It does **not** test the parent Issue's empirical H or
support an observation-reduction policy for a real GUI, app, model, or runtime.
No safety or rare-event claim follows from zero synthetic safety failures.
