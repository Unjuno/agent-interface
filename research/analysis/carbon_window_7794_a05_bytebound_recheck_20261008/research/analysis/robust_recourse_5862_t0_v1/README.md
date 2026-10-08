# Issue #5862 — belief-robust recourse T0

`PLAN.md` freezes H/T/D/C/U, including the Issue correction that existential paths do not certify advice over a belief set. `fixture.json` contains seven typed stops, sixteen finite states and all declared outcomes. `candidate.py` checks bounded common-first-action contingent policies. `audit.py` independently enumerates every state/outcome and binds the expected belief sets and dangerous replay transition. The nine local construction tests include five adversarial mutations; they are not the formal allocation.

The one-shot GitHub-hosted Docker workflow runs the frozen candidate and independent auditor in separate network-disabled containers. No recovery action is executed and no authority or coordinates are emitted. Formal results, if reached, establish only this finite abstraction; they do not show that a real GUI or human recommendation is feasible.
