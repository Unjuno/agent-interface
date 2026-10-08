# Issue #7790 — opportunity-bound preference evidence T0 A01

## H / T / D / C / U

**H:** On this finite synthetic fixture, a conservative opportunity/provenance gate identifies more explicitly consented, decision-relevant preference comparisons than DISCARD_HISTORY while emitting no comparison from forced, defaulted, agent-originated, unknown-origin, unverified-notice, or expired/opted-out traces. It returns a set of consistent orders, not a single inferred preference.

**T:** No participants, model, GUI, user data, or authority. Freeze all six strict-order hypotheses over A/B/C and ten short traces covering direct choice with a complete verified opportunity; only-one-enabled; preselected default; unverified notice; constraint-forced choice; agent action; unknown source; opposite choices in different contexts; reversal after a context-version/menu change; and expired consent. Group evidence only by principal, task, consent scope, context ID and context version. Compare naive action-frequency aggregation, opportunity-bound set-valued inference, and discard-all-history. Independently enumerate every order consistent with admissible scoped observations. Mutation probes remove an alternative, introduce a default, change actor, withdraw consent, and change context version.

**D:** PASS_METHOD_SCOPED iff candidate and independent oracle agree on every observation, scope, identified-order set and mutation; every emitted pair relation is entailed by admissible consented evidence; all observationally equivalent orders remain; invalid/forced/default/agent/unknown records emit no preference relation; and changing context version does not merge historical evidence. FAIL_METHOD on any unsupported comparison, authority claim, missed alternative order or oracle mismatch. UNCERTAIN if the finite trace omits a confound needed by the rule.

**C:** Explicit-only preference elicitation or discarding all behavior may be safer with negligible loss. Preferences may be context-specific; confirmation may still be needed for consequential choices.

**U:** Synthetic traces only. No claim that a person noticed an option, that a revealed choice is normative preference, or that context scopes generalize. No personalization, welfare, consent-quality, privacy, GUI-safety or action-authority conclusion.

## Frozen execution

Construction-only tests precede the freeze. Then run candidate and independent audit once in pinned OrbStack linux/arm64 with networking disabled, one CPU, 1 GiB memory and 64 PIDs. Source mount read-only, output directory writable. No retries or post-freeze source edits. A PASS is method evidence only.
