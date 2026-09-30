# STPA-derived feedback constraint — Issue #5327 T0

## H / T / D / C / U

**H.** In a small synthetic control structure, adding an explicit feedback-delivery constraint at the controller boundary prevents actions based on a verifier result that was produced but not delivered (or whose decision sequence is stale), while preserving action admission when a matching current PASS is acknowledged. Merely documenting the control structure does not enforce this constraint.

**T.** One deterministic synthetic finite-state run across four policies (`LOCAL_GATES_ONLY`, `STPA_MODEL_ONLY`, `STPA_PLUS_FEEDBACK_MONITORS`, `FAIL_CLOSED_UNMAPPED`) and five schedules: current PASS delivered/acknowledged; PASS produced but delivery lost; stale prior-sequence PASS acknowledged; current REJECT delivered; and action path without a control-structure mapping. Compare admission, hazard classification, false blocks, and traceability. Each row retains ordered events and derived decisions. No runtime, model, GUI, network, or external action.

**D.** `PASS_FEEDBACK_CONSTRAINT_SCOPED` iff the local-gates baseline admits at least one action on missing/stale verifier feedback; the explicit monitor rejects every such action; the matching current PASS remains admissible; current REJECT is rejected; the unmapped policy rejects the unmapped action; and an independent raw-only oracle reconciles every row/event/decision. Any contradictory safety outcome is `FAIL_*`; malformed/incomplete traces are `STOP_AUDIT_MISMATCH`. This is a synthetic counterexample demonstration, not evidence about deployed gates.

**C.** Verifier sequence IDs are strictly increasing integers; acknowledgement is current only when delivered and sequence-equal to the action's required sequence; a verifier PASS without such acknowledgement is not usable controller feedback. Backend capability and task demand are fixed true except in the unmapped control; local non-verifier gate checks are stipulated true for all mapped scenarios. These are operational assumptions, not claims about existing code.

**U.** Actual controller/backend topology, delivery semantics, sequence freshness, concurrent actors, human feedback, real hazard prevalence, control-structure completeness, and practical false-block rate remain unknown. STPA enumeration does not prove completeness or safety. No live fault injection or authority decision is authorized.

## Synthetic control structure and relation

Planner proposes an action → policy controller evaluates local gates and a verifier receipt → broker transmits the action → backend changes state → observation returns a typed effect to the controller. The safety constraint under test is: `an action requiring verification may be admitted only after the controller receives an acknowledgment for the exact current verifier decision sequence`. The prohibited control action is `ACT when receipt is missing, stale, or rejected`. This is exactly the bounded causal scenario exercised here; it is not a comprehensive STPA analysis.

`STPA_MODEL_ONLY` emits traceability labels but intentionally leaves admission behavior unchanged. `STPA_PLUS_FEEDBACK_MONITORS` enforces the declared acknowledgment predicate. `FAIL_CLOSED_UNMAPPED` additionally refuses when no control-structure mapping exists. Policies are test definitions, not runtime implementations.

## Artifacts

- `model.py`: finite schedules, policies, state and trace generation.
- `run.py`: one-shot immutable formal output.
- `audit.py`: independent raw-only reconstruction; does not import model or runner.
- `test_model.py`: construction controls, separate from formal execution.
- `FREEZE.json` and `FREEZE_COMMENT.md`: exact source/image identity, commands and decision rule.
- `results/formal-01/`: raw traces, summary, independent audit and scope report.
