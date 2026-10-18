# Evidence coordination and delegation observability

Updated 2026-10-16. These open proposals address two different limits of
distributed evidence: recipients can hold valid but incompatible histories,
and causal traces may not identify which delegated authority context owned an
event. They do not claim a current repository defect or authorize runtime,
GUI, provider, or authority changes.

## 1. Detecting split-view evidence histories — #8912

- **Status:** Open and unverified; no implementation or result is recorded.
- **Question:** Can recipients detect when one evidence coordinator gives
  different verifiers incompatible signed snapshots for the same log and
  disclosure scope? A signature or Merkle inclusion proof validates one
  presented history; it does not prove all recipients saw the same history.
- **Proposed T0:** In a finite asynchronous model with two to five recipients
  and witnesses, compare local-chain validation with witness cross-checks.
  Include valid append-only extensions, conflicting same-scope roots,
  different authorized scopes, delayed/reordered/duplicated/lost messages,
  partitions, colluding witnesses, and malformed proofs. An independent fork
  oracle should distinguish detectable forks from pairs that have not met.
- **Boundary:** Detection depends on declared honest-witness and connectivity
  assumptions. A valid proof or witness quorum establishes consistency of
  bytes/history only; it does not establish semantic truth, capture
  completeness, authorization, or GUI effect. No cryptographic or deployed
  security result exists.
- **Related work:** #6013 handles claim-scoped audit evidence, #5441
  protocol-relative acknowledgement, #5314 verifier quorums, and #5332
  assurance cases. None is treated as evidence for recipient cross-checking.

## 2. Delegation membership under concurrent traces — #8915

- **Status:** Open and unverified; no implementation or result is recorded.
- **Question:** Do event order and actor/process labels uniquely identify which
  overlapping parent delegation owns an event? Causal execution lineage,
  delegated-task membership, and attribution of an application effect are
  distinct relations.
- **Proposed T0:** Use a deterministic finite event model with overlapping
  delegations, child work, redelegation, retries, and interleaved independent
  events. Construct paired worlds with identical timestamps, event types,
  actor labels, and causal edges but different delegation membership. A
  trace-only method should report non-identifiability; a context-bound method
  should reconstruct valid memberships and reject or mark unknown missing,
  forged, duplicate, stale, or conflicting contexts.
- **Boundary:** This is a simulator-only identifiability test. A membership
  label does not prove intent, policy compliance, causation, or task success;
  context propagation does not prove complete mediation. No runtime, GUI,
  model, or network result is claimed.
- **Related work:** #47 and #1211–#1241 study actor attribution; #15 studies
  causal observation/action/effect lineage; #8587 reconciles event ledgers with
  source traces. Their estimands remain distinct from delegation membership.

## 3. Multi-source event-trace reconciliation — #8587

- **Status:** A01 `PASS_METHOD_SCOPED` on a finite authored fixture; open PR
  [#8747](https://github.com/Unjuno/agent-interface/pull/8747) remains
  OPEN/DIRTY. No real GUI source-completeness or effect claim is established.
- **Observed result:** The one-shot candidate and independent raw-only auditor
  each exited 0 with no retries. On 15 cases, the auditor localized all eight
  identifiable boundary faults, retained missing-correlation and incomplete-
  coverage cases as UNKNOWN, and made zero false localizations on five benign
  controls. Cross-source reconciliation found 8 faults, compared with 1 for
  client-ledger-only and 0 for final-state-only comparison; concurrent source-
  order inversion remained incomparable. All five frozen mutations were
  rejected.
- **Interpretation:** This supports only the frozen event-fixture method.
  Source disagreement localizes a measurement boundary; it does not prove a
  GUI event stream is complete, establish semantic effect or task success, or
  grant action authority. The concurrent-order control also rejects invented
  causal ordering where the source traces provide no relation.
- **Relations:** #6310 tests source-complete frontiers for a scoped no-change
  claim; #2722 tests reactive event lineage under timing/focus faults; #2317
  tests mediated dependency-receipt coverage; #5716 studies workflow
  conformance under incomplete logs. These address different estimands.

## Routing

Keep these hypotheses and their evidence separate unless a future owner freezes
a test with the same estimand and controls. Split-view detection and ambiguous
delegation membership remain unverified, with no associated PR, branch, or
experiment result. The #8587 result is finite event-fixture evidence only.
Detected forks, ambiguous membership, and trace discrepancies are evidence
about history consistency or measurement coverage, never grants of action
authority.
