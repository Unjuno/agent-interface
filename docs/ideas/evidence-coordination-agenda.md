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

## Routing

Keep both hypotheses separate unless a future owner freezes a test with the
same estimand and controls. Neither proposal has an associated PR, branch, or
experiment result as of this update. Any detected fork or ambiguous membership
would be evidence about history consistency only, never a grant of action
authority.
