# Issue #7678 successor A02 — four-route certificate manipulation audit

## H / T / D / C / U

**H:** In the frozen four-route, two-principal fixture, at least one admissible unilateral report changes the #6274 possible-frontier certificate. Under the explicitly declared utility (best true-order tier available in the displayed set), an exhaustive check over the frozen information cells will either find a safe beneficial report or justify a null for this finite domain.

**T:** Enumerate six preregistered complete true weak orders per principal (four cyclic strict orders covering each route as the unique top, plus two tied orders), every unilateral report in a finite 92-report domain (all 75 complete weak orders over four routes, all distinct projections onto `{a,b,c}`, `{a,b}`, and the empty comparison mask), and every one-principal deviation for all 36 truthful profiles. Recompute the exact frozen #6274 certificate for each case. Evaluate full-information cells (exact peer order) and partial-information cells (peer order projected to `{a,b}`). Run candidate once and the separate #6274 independent rank-vector oracle once. No people, models, GUI, network, live workspace, GPU, or WSLc.

**D:** `PASS_METHOD_SCOPED` iff the complete 6,624-row profile/deviation matrix is emitted; the independent rank-vector oracle exactly reconstructs every certificate and information-cell utility; at least one certificate changes under an admissible report; all reports leave joint grants and protected constraints unchanged; revocation, protected-exclusion, incomplete-comparison/UNKNOWN, and no-decision-right controls pass; and safe-benefit is reported exactly (including an exhaustive null). Any mismatch or authority/constraint mutation is `FAIL_METHOD`; a missing frozen input or incomplete matrix is `HOLD`.

**C:** This expands A01's three-route fixture to four routes and adds tied true weak orders. The finite six-order type set is deliberately bounded; outcomes may depend on that selection, the certificate rule, report masks, displayed possible frontier, and best-available-route utility. The diagnostic does not claim that narrowing a choice set is itself a benefit.

**U:** Synthetic exhaustive evidence only for the exact frozen types, reports, peers, and utility. No human manipulation prevalence, fairness, consent, legal/privacy status, GUI safety, production, or general strategyproofness inference. No proposal to hide information or alter the decision rule.

## Freeze and execution

- Allocation: `PREFERENCE-MANIPULATION-7678-A02-FOUR-ROUTES-20261005-01`.
- Source base: current main `f60752d0fb71595363a80977636ca74c1fd10b21`.
- Canonical candidate and independent oracle: Issue #6274 files at commit `c837ad535eed085d95744ad0a9680535a5bb7143`; exact blob and byte hashes are in `FREEZE.json`.
- Fixture, candidate, auditor, and command hashes are frozen before candidate execution.
- Run exactly one native CPython candidate, then one independent oracle. Any post-start failure is retained; no retries. The previous A01 allocation remains HOLD and is not invoked or changed.
- WSLc is not used: the current #6693/#6389 owner record forbids further WSLc operations while unknown clients remain unresolved. This allocation is pure local CPU enumeration and does not need a container.

## Decision boundary

This measures whether the declared certificate is sensitive to the tested reports and whether the stated set utility improves over the selected information partitions. It does not assign preferences, select an effect, change a grant, or authorize reduced transparency.
