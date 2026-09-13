# Saved-effect evidence attached to live finalization

Candidate `interactive_v22.py` uses `finalization_v2.py` to close admission, sample
Calc saved-cell evidence, run the existing independent evaluator, and publish the
evaluation with a separate `effect` field. Retained finalization status also holds
the effect, including if later evaluation/publication fails. Other apps retain
their previous scoring flow. This applies only to `finish_after` finalization;
plain `finish` without a final program retains the old behavior.

Two scripted private X11 Calc episodes use seed 991022. Save enters 532/590,
saves and confirms Excel; unsaved submits Return on the initial empty workbook.
Both programs finish completed with verified release. The first reports VERIFIED
and saved [532,590]; the second CONTRADICTED and saved [null,null]. Snapshot hashes
match the independently opened workbook copies. Both combined evaluations are
observed by the subprocess supervisor and have flush receipts; this is not proof
of assistant comprehension.

| Case | Terminal to effect computed | Terminal to evaluation emit started |
|---|---:|---:|
| Save | 23.476 ms | 27.924 ms |
| Unsaved | 15.058 ms | 3023.367 ms |

The unsaved outcome exposes a delivery bottleneck: the effect is known before
the existing evaluator completes its wait. The effect currently travels with
that evaluator's result, so this candidate does not yet remove the delay.
Next evaluate separate early effect publication, keeping output confirmation,
retained failure state and final independent scoring distinct. Do not describe
these two single scripted episodes as assistant speed or a controlled speedup.

The initial probe used `max_ms` instead of the required `timeout_ms` for settle
and was rejected before task input. `results/live-saved-effect-01` retains that
failure and cleanup output. Corrected probe v2 uses a new output cohort,
`results/live-saved-effect-02`; source v1 remains unchanged.

`audit_live_saved_effect.py` verifies listed runtime hashes, 14 exact public
AIT/PNG frames, result retention, ordering and output receipts. Three additional
callback tests preserve UNKNOWN on normal publication, evaluator failure and
unconfirmed publication. These fault cases are callback tests, not live missing
file injection. Audit output is `results/live-saved-effect-audit.json`.

The contract still checks declared first-sheet saved cells, not action causation,
the entire workbook or future writes. Admission closure only stops this executor;
it does not stop application background writes. A match can predate the action.
No automatic retry, input authority extension, default promotion or freeze credit.
