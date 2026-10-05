# Issue #7678 T0 — manipulation sensitivity of a choice certificate

## H / T / D / C / U

**H.** In a finite shared-effect fixture, a unilateral misreport can change the #6274-style frontier/certificate. We test the stronger claim that a misreport can safely improve the reporter's presented opportunity set: among routes shown to the named decision-maker, the reporter's best true-ranked route is weakly better in every peer-preference world the reporter considers possible and strictly better in at least one.

**T0.** Invoke the exact `evaluate` function from the frozen #6274 source blob, without calling its original study `main`, writing to its old result directory, or running its old auditor. Use two synthetic principals, three identical requester-effect routes, all 13 complete weak orders as true types, and every report in a predeclared finite domain: the 13 complete weak orders, their projections onto each of the three single-pair masks, and the empty report. Enumerate every unilateral report for both principals against every truthful profile. The full-information partition knows the peer's exact type; the partial-information partition observes only the peer's `a`-versus-`b` comparison. A separate rank-vector oracle reconstructs every completion, frontier and manipulation comparison from the frozen fixture and candidate output.

The displayed opportunity set is explicitly the certificate's **possible frontier**. Its ordinal utility for a reporter is the best (lowest-tier-number) route available in that set under the reporter's true weak order. This is a deliberately narrow, fully specified set-utility; it is not a prediction of how a human decision-maker chooses. A named delegate's output is recorded separately and remains an authorized decision right.

Negative controls: a revoked grant cannot be restored by a preference report; a protected constraint excludes its route before ranking; omitted comparisons retain multiple completions and uncertainty; and a changed frontier is never reported as an automatically chosen effect when no decision right is declared.

**D.** `PASS_METHOD_SCOPED` iff the independent oracle agrees on every truthful/deviation certificate in both information partitions, detects at least one report-dependent certificate change, correctly classifies every safe beneficial deviation (including a justified exhaustive null), and all four controls pass. Any mismatch or authority/constraint violation is `FAIL_METHOD`; an unfreezable order/report/information or set-utility semantics is `HOLD`. A null under this declared utility does not establish universal strategyproofness.

**C.** Truthful reports may preserve a reporter's top-ranked route in this Pareto-style frontier while some deviations remove it, even when no deviation improves the declared best-available-route utility. The delegate's own decision and human reactions to a displayed set are outside the certificate's deterministic output.

**U.** Three alternatives, two principals, hand-authored finite weak orders, one partial-information signal and a best-available-route set utility. This says nothing about actual people, manipulation prevalence, fairness, consent, legal/privacy status, GUI safety, strategic coalitions, hidden consequences, or production behavior.

## Frozen procedure

- Allocation: `PREFERENCE-MANIPULATION-7678-T0-20261005-01`.
- Current `main` at source freeze: `3dbbda05eb8d5067ee2c2969615e472a0f20f562`.
- Canonical certificate source: `research/analysis/preference_explicit_choice_6274_t0_20261002/candidate.py` at the frozen commit; SHA-256 is in `FREEZE.json`.
- Fixture: `fixture.json`; finite domains and report masks are fixed before the formal run.
- Candidate and independent auditor each run once, sequentially, on candidate exit 0 only. Retry count 0. The formal auditor recomputes per-deviation certificates and the declared full/partial information cells; D passes only when its independent signatures match all candidate rows, the report-sensitivity guard and four negative controls pass, and safe opportunity-set gains are correctly reported (including an exhaustive null).
- Environment: Windows host / CPython 3.11.9 / one standard-library CPU process / no network, model, GPU, GUI, shared data, or live workspace. WSLc is not used because Issue #6693's latest owner update explicitly says to make no further WSLc list/run calls while existing unowned clients remain unresolved. This is a host-only method result, not container evidence.
- Formal output is confined to this package's `results/formal-01/`; historical #6274 files and result directories are read-only.

## Decision boundary

The finite result can show whether this certificate changes under reports and whether a report improves the stated opportunity-set utility over the enumerated information cells. It cannot assign a preference, select an effect, change a grant, or justify reducing transparency. A confirmed no-manipulation result is scoped only to the frozen profiles, report domain, information partition and utility above.
