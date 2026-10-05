# Issue #7790 — T0 A01 result

## Outcome

**PASS_METHOD_SCOPED** for this finite synthetic method test only. Candidate and independent exhaustive auditor agreed exactly. The result makes no claim about real people's preferences, notice, consent quality, privacy, welfare, generalization, personalization, or action authority.

## Question and design

The experiment asks whether an opportunity- and provenance-gated inference can retain only comparisons entailed by verified, consented direct choices made when all alternatives were available, while separating principal/task/consent/context/version scopes. The fixture has all six strict orders over A/B/C and ten synthetic scenarios (12 events). No participants, model, GUI, user data, or live preference-learning were used.

Five events were admissible: `e01`, `e08a`, `e08b`, `e09a`, and `e09b`. They produce five separate scopes and 15 surviving order rows (three orders per one-comparison scope). `delivery/v1` yields A>B while `appearance/v1` yields B>A; they remain separate. `preferences/v1` yields A>B and `preferences/v2` yields B>C; the context version change also remains separate. Every relation is entailed by every retained order, and no single order is selected.

The naive action-frequency baseline aggregates every recorded action, including forced/default/agent/unknown/expired cases, and reports A=8, B=4; it therefore conflates confounded events and scopes. `DISCARD_HISTORY` yields zero preference comparisons by definition. The opportunity-bound method retains only the five admissible scope-local comparisons. Neither baseline nor candidate output is authority.

All five mutations behaved as expected: removing an alternative, adding a default, changing actor, and withdrawing consent each yielded no identified comparison; changing context version split the scope. Local construction CI passed 5/5 tests before freeze. Formal candidate and auditor each ran exactly once in the frozen container and exited 0; the auditor returned `PASS` (5 scopes, 15 order rows, 5 admissible events, 5 mutations). The first GitHub Actions run exposed that the test assumed the process working directory; only the test harness was changed to resolve `fixture.json` relative to its own file. Frozen candidate, oracle, fixture, image, and formal outputs remain unchanged; the focused suite and checksums were rerun locally after this portability-only fix.

## Limits and next test

This is exhaustive only over the declared three-option strict-order domain and the finite trace schema. It does not establish that telemetry can validly prove notice, availability, actor identity, consent scope, or context boundaries. Repeated contradictory observations within one identical scope, missing/duplicated event IDs, malformed sets, cyclic constraints, partial captures, and consent-scope expiry mid-trace need successor tests before broader claims. The Issue remains open for further validation.

## Reproduction

Read `PROTOCOL_A01.md`; source, fixture, image, and output hashes are recorded in `RUN.json` and `SHA256SUMS`. Container: `linux/arm64`, Python 3.12.11 slim pinned by base digest, network disabled, 1 CPU, 1 GiB memory, 64 PID limit, read-only root/source mount, writable results mount. Raw candidate JSON and independent audit JSON are preserved under `results/`.
