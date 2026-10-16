# Human evaluation validity

These ledger entries preserve distinct human-evaluation questions. None authorizes a participant study or establishes a human behavioral effect.

## Recording-salience reactivity — #8022

- **Status:** on hold
- **Source:** [Issue #8022](https://github.com/Unjuno/agent-interface/issues/8022); [merged protocol-audit PR #8128](https://github.com/Unjuno/agent-interface/pull/8128)
- **Idea:** In a future fully consented human–agent evaluation, compare an explicit pre-task reminder that traces will be reviewed with an equal-attention neutral reminder. Keep consent, actual capture, task, tools, incentives, evaluation, and withdrawal rights identical. The target is the incremental effect of reminder salience among informed participants, not covert observation or a universal Hawthorne effect.
- **Outcome:** The no-human A01 audit recorded `HOLD_NO_AUDITABLE_PROTOCOL`: the Issue described the required invariants but lacked concrete consent text, capture configuration, task/scoring materials, reminder scripts, missingness handling, and a preregistered practical threshold. No participant or human outcome was involved. The [retained audit](../../research/analysis/recording_salience_8022_protocol_audit_a01_20261005/RESULT.md) leaves the Issue open; a future human pilot needs auditable protocol materials, ethics approval, voluntary informed consent, and privacy minimization.

## Faded agent demonstrations and later unaided transfer — #6600

- **Status:** unverified human-transfer hypothesis; two synthetic method ledgers passed.
- **Source:** [Issue #6600](https://github.com/Unjuno/agent-interface/issues/6600); [merged demonstration T0 PR #6730](https://github.com/Unjuno/agent-interface/pull/6730); [merged practice-order T0 PR #8457](https://github.com/Unjuno/agent-interface/pull/8457); [demonstration report](../../research/analysis/faded_demonstration_6600_t0_orbstack_20261002/README.md); [practice-order report](../../research/analysis/faded_demonstration_practice_order_6600_t0_a01_20261008/REPORT.md).
- **Idea:** Test whether an explicitly optional, source/effect-verified faded agent demonstration improves later unaided performance on a held-out related GUI task, while preserving opt-out and safety.
- **Outcome:** The demonstration T0 returned `PASS_METHOD_SCOPED` on nine synthetic cases; the fixed-dose practice-order T0 independently reconstructed two six-slot arms and rejected all six mutations. Neither tested a learning effect. There were no participants, GUI actions, or human outcomes. Any T1 needs its own reviewed, consented, privacy/accessibility-aware protocol and independent task-effect scorer.

## User-relative benefit with chosen settings — #6593

- **Status:** unverified user-benefit hypothesis; synthetic accounting method passed.
- **Source:** [Issue #6593](https://github.com/Unjuno/agent-interface/issues/6593); [merged T0 PR #6651](https://github.com/Unjuno/agent-interface/pull/6651); [retained report](../../research/analysis/user_relative_benefit_6593_t0_v1/REPORT.md).
- **Idea:** Keep each participant's chosen assistive-technology settings and preferred pace when comparing assisted offers with that person's unaided workflow; do not use a pooled human-tempo comparison as a proxy for individual benefit.
- **Outcome:** `PASS_METHOD_SCOPED` reconstructed seven synthetic cases and 13 assigned pairs, including a stipulated pooled-versus-within-person time-direction reversal. Refusals, missing outcomes, changed settings, and under-supported pairs remained visible. This validates finite accounting only; no participant, accessibility, causal, or population benefit was measured. Any human study needs separate consent, privacy/accessibility review, and resource ownership.
