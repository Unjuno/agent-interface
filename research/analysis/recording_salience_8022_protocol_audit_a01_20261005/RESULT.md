# Issue #8022 — no-human protocol audit A01

**Result: HOLD_NO_AUDITABLE_PROTOCOL.** The first ethical rung was executed as a bounded document audit of the open Issue specification on 2026-10-05. It did not pass the protocol gate: the Issue states the intended controls and treatment contrast, but does not contain the concrete protocol artifacts needed to verify that those controls are implemented identically. No participant study, human outcome, or causal effect was run or inferred.

## Frozen question and decision rule

- **H:** Among fully informed participants, an explicit pre-task reminder that traces will be reviewed changes at least one preregistered outcome by a practically meaningful amount versus an equal-attention neutral reminder; direction is unspecified.
- **T0 audited:** Before any human study, verify a concrete protocol in which consent, recording/capture, task, incentives, evaluation and withdrawal rights are identical, with only the prespecified reminder differing.
- **D:** `METHOD_PASS_SCOPED` only if the concrete materials establish every invariant and the single intended contrast. `HOLD_NO_AUDITABLE_PROTOCOL` if materials are absent or any invariant cannot be checked. T0 cannot establish human reactivity.
- **C:** wording/attention, demand characteristics, anxiety, workload, learning/order and self-selection could explain a future observed difference; no effect is also plausible.
- **U:** Any future result would be limited to the specified task/population/reminder and could not establish a universal Hawthorne effect or justify covert recording.

Source frozen for this audit: [Issue #8022](https://github.com/Unjuno/agent-interface/issues/8022), retrieved 2026-10-05; Issue `updated_at=2026-10-05T05:52:49Z`. No changes were made to the Issue text.

## Audit performed

I mapped each required invariant in T0 to a concrete inspectable artifact in the Issue. “Requirement stated” is not treated as “protocol verified.”

| T0 invariant | Issue states the invariant? | Concrete auditable material supplied? | Finding |
|---|---:|---:|---|
| Complete consent and data-handling explanation in both arms | Yes | No consent text or delivery procedure | HOLD |
| Same actual capture/recording in both arms | Yes | No capture configuration or verification record | HOLD |
| Same fixed task and tool access | Yes | No task script/fixture specification | HOLD |
| Same incentives/compensation | Yes | No allocation or compensation procedure | HOLD |
| Same evaluation and independent scoring | Yes | Outcomes are named; no scoring rubric/blinding procedure | HOLD |
| Same withdrawal rights and handling of withdrawn/missing attempts | Yes | No participant-facing wording or data disposition procedure | HOLD |
| Sole contrast is pre-task salience reminder; equal attention | Yes | No exact reminder/control scripts or equivalence check | HOLD |
| Primary outcomes and meaningful threshold/uncertainty method frozen before enrollment | Partly | Outcomes named; threshold, estimator and interval/precision rule absent | HOLD |
| Repeated-measures order/carryover and all-attempt accounting | Yes, as requirements | No randomization/counterbalancing schedule or analysis specification | HOLD |
| Privacy minimization / no personal content | Yes | No fixture/data-field inventory or capture audit procedure | HOLD |

### Falsification checks

The issue prose was checked against the gate as written:

1. A statement that both arms receive complete consent is insufficient to verify the consent artifact or whether it differs; therefore the gate cannot pass.
2. Naming task success and completion time is insufficient to reproduce scoring or determine the predeclared practically meaningful difference; therefore the estimand/decision rule is not frozen.
3. Saying capture is identical is insufficient without a capture configuration or audit procedure; no arm-level capture parity can be checked.
4. The proposed contrast is ethically bounded in principle: the issue explicitly forbids covert collection and requires complete consent in every arm. This design constraint is retained; it does not cure the missing protocol materials.

These checks support HOLD, not a finding that the proposed design is unethical or that any human behavior changes under observation.

## Evidence and limits

- Executed action: inspected the complete Issue #8022 specification and applied the finite T0 artifact checklist above.
- Outcome: **HOLD_NO_AUDITABLE_PROTOCOL**; no method PASS and no human study authorization.
- No container was used: this is a document-level pre-study audit, not a local CPU experiment. OrbStack image inspection had already failed in the active environment with a content-store “operation not supported” error; no retry, image pull, or daemon change was attempted.
- No raw participant data, private content, GUI input, or recording was collected.
- Independent second-person audit: **not performed**. This report must not be described as independently audited.
- Local CI: not applicable to this standalone Markdown audit; no code or runtime contract changed.
- The next eligible gate is to supply concrete consent/data-handling text, equal-attention reminder scripts, fixed task/scoring materials, capture-parity verification, withdrawal/missingness handling, and a preregistered practical threshold/uncertainty plan. Human enrollment remains out of scope absent ethics approval and voluntary informed consent.

This A01 preserves a scoped STOP/HOLD result. It does not replace Issue #8022 or claim the research hypothesis was tested.
