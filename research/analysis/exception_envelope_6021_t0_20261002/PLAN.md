# Issue #6021 T0 — cumulative exception-envelope audit

## H / T / D / C / U

- **H:** A finite history-aware envelope enumerator detects (i) a cross-product permission created by composing separately scoped field relaxations and (ii) an expired exception copied into a later current snapshot, while preserving valid disjoint/superseding exceptions and never waiving a hard prohibition.
- **T:** Enumerate all action × route × task × source-generation × age × target × effect-truth tuples (256 rows) across six versioned fixtures. Compare each mechanically composed scope with the union of its exact single-exception scopes; track waiver authentication, explicit scope, expiry, supersession, hard invariants and claim-evidence history. Independently implement the enumerator.
- **D:** `PASS_METHOD_SCOPED` only if the cross-product and expired-copy controls are flagged, valid disjoint and authenticated supersession remain admitted, hard EXPORT prohibition is never relaxed, and post-outcome evidence relaxation is detected. Scope/expiry/order/issuer/negative-result mutations must fail or yield UNKNOWN.
- **C:** No-exception policy-as-code or mandatory human diff review may be simpler and more reliable. This checker does not replace governance, authenticated histories, or policy owners.
- **U:** All roles, scopes, precedence and histories are synthetic. The checker cannot establish off-repository overrides, informal norms, authenticated real actors, or organizational drift frequency. A flagged expansion is not automatically unsafe; human review is still required.

## Method boundary

Rasmussen (1997), [DOI](https://doi.org/10.1016/S0925-7535(97)00052-0), frames safety in terms of evolving sociotechnical constraints and boundaries; it does not validate this finite auditor. *The Normalization of Deviance in AI Development* ([arXiv:2609.05749](https://arxiv.org/abs/2609.05749)) already applies the broad organizational-drift analogy to AI. Novelty here is limited to an independently enumerable versioned authority/evidence envelope.

## Execution

Base commit: `279ee4aee96c5646360239409931821726566aa2`; additive package path. Construction mutations before freeze, then one candidate and one independent audit invocation. Host CPython only; no Docker isolation claim (Engine unavailable). No model, network, GUI, application, participant, or live policy change.
