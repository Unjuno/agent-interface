# Issue #6342 T0 preregistration

Allocation: `REACTANCE-SAFE-STOP-6342-T0-ORB-20261003-01`
Base: main commit `43f7cd88d91af05036fae2100ec4e155c59e105c`
Branch: `research/reactance-safe-stop-6342-t0-orbstack-20261003`
Evidence path: `research/analysis/reactance_safe_stop_6342_t0_20261003/`

## H / T / D / C / U

- **H:** Matched directive and autonomy-supportive safe-stop cards can preserve identical evidence, mandatory stop, forbidden-retry rule, and allowed safe actions while a bounded independent checker rejects cards that imply a forbidden retry or an unverified success.
- **T:** Method-only, no-participant T0. Freeze four synthetic cases (uncertain save delivery, stale target, partial edit, verified-success control), two framing variants per case, and two deliberately unsafe mutation controls. Run one card renderer and one independently implemented checker in separate OrbStack containers. T0's full pass gate also requires a separate blinded reviewer for the eight matched pairs; this workspace has no authorized independent human reviewer, so absence of that review must be recorded as HOLD, not inferred from code checks. Construction tests do not invoke the formal renderer or auditor.
- **D:** `PASS_METHOD_SCOPED` only if all eight pairs have identical non-framing fields and allowed actions, equal framing-line word counts, identical hard-stop/receipt/accessibility structure, both unsafe controls are rejected, the verified-success control is not mislabeled unresolved, and the independent reviewer finds no changed permission, urgency, evidence claim, or success implication. Any false-success/unsafe-retry acceptance is `FAIL_METHOD`; missing semantic review or an ambiguous card is `HOLD`.
- **C:** Equal fields and word count do not establish equal comprehension or reading time. Reviewers may interpret wording differently; the correct result can be HOLD rather than forcing parity.
- **U:** No participant, model, audio, GUI, actual behavior, reactance, safety effect, latency, or human-benefit evidence. Passing T0 establishes only that the proposed T1 card contrast is internally auditable enough to consider; T1 needs separate consent/privacy/accessibility and task-effect review.

## Frozen protocol

Input fixture: `cards.json`; renderer: `render_cards.py`; independent audit: `audit_cards.py`. Python standard library only. Candidate maximum 1 invocation, auditor maximum 1 invocation, retries 0. The renderer emits eight treatment cards and two planted negative controls. The auditor independently reconstructs the expected scenario/action contract from constants separate from the renderer, compares paired cards, and classifies each negative control. A reviewer receives the pair texts without arm names or expected labels and the frozen review rubric in `review_bundle.json` after candidate output is retained.

The four case truths are limited to these source-bound synthetic receipts: save completion unresolved; target observation stale; partial edit with one confirmed and one unresolved field; and fully verified success. The card never receives hidden simulator truth beyond the receipt text. Each unresolved case blocks the consequential action and offers only its frozen safe next steps. The success control reports only the independently verified effect stated in its receipt.

Runtime: OrbStack Docker Engine 29.4.0, local image `python@sha256:c4634f578a412db396771b61b064c6e546c9d6414c7fb5b1b05d5871f1885f7b` (`linux/arm64`). No pull/build/install/network. Each formal stage runs in a distinct named container with read-only root and input, `--network none`, 1 CPU, 256 MiB configured memory, 64 PIDs, all capabilities dropped, `no-new-privileges`, and non-root UID 1000. Host cgroup/swap state and actual enforcement are recorded separately; configuration alone is not proof of effective enforcement. The unrelated running container `unjuno-native-ci-6092` is out of scope and must not be inspected beyond its already observed name/status, touched, stopped, or joined.

Formal results are immutable first outcomes. No regeneration, wording changes, retries, or threshold changes after candidate execution. Any correction requires a separately allocated successor and leaves this result intact.
