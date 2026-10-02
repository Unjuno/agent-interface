# Issue #6565 — T0 candidate-card parity and mutation challenge

## Lineage and scope

This is a narrow T0 method successor to Issue #6565 and its 2026-10-02 framing clarification. It does **not** re-run a human study (none has occurred), infer any presentation effect, or claim that constraint-first reduces false acceptance. It checks whether a frozen, source-bound task constraint and exact candidate-effect footprint remain factually identical across truthful presentations, and whether a separate auditor detects planted confounds. Agent origin stays explicit in every arm. This isolates only construction/provenance readiness; human influence remains untested.

## H / T / D / C / U

**H.** For a finite authored set of disposable candidate cards, a canonical effect/constraint contract can be presented in preview-first, constraint-first, and neutral-facts-first orders without changing underlying facts, authority, source disclosure, or candidate digest; an independent auditor rejects planted swaps, leaked oracle labels, unsupported recommendation claims, missing provenance, and digest changes.

**T.** Standard-library-only deterministic fixture. Four task cases (valid, wrong recipient, wrong format, genuinely new fact with preference revision unspecified) crossed with three truthful presentation policies. Each card retains canonical source task, constraint oracle, candidate effect, allowed effect, agent provenance, neutral facts, and presentation event sequence. A construction generator emits all 12 rows. An independent raw-only auditor re-derives factual parity and fixed expected violations without importing candidate code. Six mutation controls each alter exactly one contract dimension. No participants, UI rendering, model, user data, or live effects.

**D.** `PASS_METHOD_SCOPED` iff (1) every clean presentation policy preserves the same case facts, constraint verdict, agent-origin disclosure, and candidate digest; (2) the preference-revision case remains `UNSCORABLE_PREFERENCE`, not coerced to violation/valid; (3) all six mutations are rejected; and (4) every candidate row is independently reconstructed exactly. Any false parity, unsupported recommendation, oracle leakage, provenance loss, digest drift, or invented preference outcome is `FAIL_METHOD`. Incomplete source/contract semantics is `HOLD`.

**C.** Identical wording/order without pre-elicitation may be sufficient; card-level parity does not establish salience, comprehension, memory, or causal anchoring. External advice-order literature is direct prior art; no novelty is claimed for generic order or source framing.

**U.** Synthetic card construction only. No person, acceptance response, comprehension, burden, preference, real GUI preview, consent, or human benefit is measured. A method PASS is not H-pass evidence and does not authorize T1.

## Frozen cases and policies

Cases: (a) allowed target/recipient/format; (b) recipient contradicts explicit source constraint; (c) format contradicts explicit source constraint; (d) new neutral fact may support a changed preference, whose value is not fixed by the original constraint. Policies vary sequence only: `PREVIEW_FIRST`, `CONSTRAINT_FIRST` (constraint recall before candidate), `NEUTRAL_FACTS_FIRST` (neutral facts before same candidate). Every arm discloses `agent-origin: true`, shows the same canonical effect and neutral facts, and uses the same authority state. Any wording differences are limited to ordering; no quality recommendation or human/peer attribution is permitted.

Mutation controls: changed recipient; changed format; removed source attribution; injected quality endorsement; exposed hidden oracle label; altered candidate digest. Candidate is deterministic and intended to emit conforming cards; mutants exist only as auditor test inputs and are not part of the formal candidate allocation.

## Execution

Run the construction/mutation suite on the host, then once in a fresh network-disabled OrbStack container using the locally cached digest-pinned Python 3.12 image. Formal candidate and auditor each get one fresh, distinct container; candidate raw output is immutable and auditor independently reads it. No pulls, network, retries, or changes to the pre-existing `unjuno-native-ci-6092` container. Preserve exact commands, image/context/limits, exit statuses, logs, raw hashes, audit, and limitations. Any launch or audit failure consumes the allocation; no retry.
