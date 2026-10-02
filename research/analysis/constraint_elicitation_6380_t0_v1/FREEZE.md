# Issue #6380 T0 — counterexample-driven constraint elicitation method

## Intake and non-overlap

- Parent: [Issue #6380](https://github.com/Unjuno/agent-interface/issues/6380), an open unverified proposal.
- Fresh base: `893f7dc78ef814b1d5533b45b358a069f884e65c` (current main at intake).
- Existing adjacent issues read: #12 defines task/oracle contracts; #5951 preserves already-stated constraints; #5749 asks preference among admissible outcomes; #5805/#5836 address multi-principal authority and authenticated confirmation; #5944 is post-result contestation; #5990 is longitudinal representativeness. This T0 tests only finite method/provenance semantics for discovering a scripted hidden constraint before contract freeze.
- GitHub search for #6380, “unstated task constraints,” “counterexample-driven elicitation,” and “hidden constraint” found no competing T0 owner/PR. Branch search found no #6380 branch and open-PR search found none.
- New additive branch: `research/constraint-elicitation-6380-t0-20261002-893f7dc`; path `research/analysis/constraint_elicitation_6380_t0_v1/`.

## H — hypothesis

In this finite scripted method fixture, a frozen counterexample prompt can expose a respondent-authored hidden forbidden-effect clause that is absent from the original request, while preserving explicit source clauses and keeping unauthorized, privacy-blocked, absent, stale, and unanswered responses from changing the contract or minting action authority. The method may use fewer questions than the exhaustive checklist; this is not a human-effectiveness hypothesis.

## T — treatment

Eight fixed synthetic vignettes × four policies = 32 rows: `SOURCE_ONLY`, `GENERIC`, `COUNTEREXAMPLE`, `CHECKLIST`. The same deterministic respondent oracle and versioned task request are applied to each policy. Hidden truth cards are kept separate from task request and abstract scenario catalog. The explicit-prohibition vignette is not credited as newly discovered. Other controls include harmless/no-hidden-constraint variation, conflicting/unauthorized respondent, missing respondent, privacy-restricted scenario, no answer, and stale question after task revision.

This is a no-model, no-human, no-GUI, no-network, no-effect experiment in a pinned WSL Podman container. The candidate executes once. A separate standard-library-only auditor executes once after candidate success. No retries, replacements, answer tuning, or output edits. Raw candidate, audit, source hashes, exact command/container identity and scope are retained.

## D — gates

`METHOD_PASS_SCOPED` only if all 32 policy/vignette rows are present exactly once; source-origin clauses retain source provenance; only authenticated, matching, current, privacy-eligible respondent confirmations add hidden clauses; no-answer/unavailable/stale/privacy/unauthorized remain unresolved; no fabricated clause or permission appears; and all rows mint zero action authority. Independent audit must reconstruct the matrix from frozen inputs without importing candidate code and reject at least six planted mutations. A discrepancy, missing row, false addition, privacy leak, erased source clause, unsafe revision or any authority mint is `FAIL_METHOD`; infrastructure failure is `STOP/HOLD`, with no rerun.

Record question count and hidden-constraint coverage descriptively only. Scripted responses make coverage partly defined by construction; this cannot establish elicitation utility, human recall, lower interruption burden in practice, completeness or safety.

## C — caveats

The finite oracle is intentionally transparent and hand-authored; its “hidden constraint” is not natural human ground truth. Scenario-to-question mapping is fixed, not learned. This method fixture cannot demonstrate preference fidelity, consent, respondent identity in real systems, privacy-safe language, stakeholder consensus, real task effectiveness or causal benefit. A T1 human study would need separate user authorization, independent pre-elicitation constraint authoring/adjudication, voluntary participants, accessibility/privacy safeguards and preregistered burden/failure criteria.

## U — open boundary

T0 can close only this protocol/provenance slice. Whether counterexample-driven prompting improves valid discovery over a generic question at bounded priming/false-addition/interruption cost remains untested. No permission, execution, product or safety claims follow.
