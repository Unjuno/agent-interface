# Issue #5306 — deterministic VOI construction probe

**Disposition: CONSTRUCTION_AUDIT_PASS_GATE_FAIL.** This is a retrospective host-side harness-construction probe only, not a preregistered formal allocation, empirical result, or evidence for the Issue hypothesis. The final source was iterated after construction failures; no claim of pre-run source freeze is made.

## H/T/D/C/U

- **H:** Evidence-dependent stop/continue may reduce non-mandatory verifier work while a shared hard reducer preserves false-allow and required YIELD behavior.
- **T:** Replay the same positive/negative, ambiguous, stale, ontology-gap, deadline-infeasible, and correlated-duplicate toy cases under fixed, deterministic-selective, and VOI arms. Separate planning rows from held-out rows. Audit reducer, cost, false allows, and YIELD independently.
- **D:** Runnable standard-library Python probe; retained raw JSON and separate audit JSON; command, hashes, failed construction history, and scope record. Passing the constructability check is not the preregistered scientific PASS gate.
- **C:** Hand-authored deterministic transitions, tiny sample (3 planning / 6 held-out), oracle-like exact signal, arbitrary loss/cost units, and no temporal measurements. These can make the VOI policy look better by construction.
- **U:** Calibration under distribution shift, correlation beyond one labeled duplicate, non-deterministic evidence quality, real verifier costs, and residual benefit over a competitive selective baseline remain unanswered.

## Execution and results

Host: Windows 11 x64, Python 3.12.10. Docker Desktop 28.5.1 is healthy (`desktop-linux`); it was **not used** because no fresh exact container-lane assignment existed. No model, GUI, network, external effect, or formal allocation was used.

Commands:

```powershell
python .cache-memory-lab/5306-construction/voi_probe.py > .cache-memory-lab/5306-construction/raw.json
python .cache-memory-lab/5306-construction/independent_audit.py > .cache-memory-lab/5306-construction/audit.json
```

The final replay emitted 27 policy/case rows. Independent accounting/reducer checks reported zero structural errors. On six hand-authored rows labeled held-out, fixed and selective each used 9 calls / cost 21; VOI used 6 calls / cost 9. All had loss 36, zero false allows, and two required stale/ontology-gap YIELDs. The planning split (three rows) similarly gave zero loss for all arms and calls/cost of 9/26, 7/18, and 6/13 for fixed/selective/VOI. Since neither the source nor the split was frozen before execution, these are descriptive harness outputs only.

This apparent benefit is **not a research finding**: VOI's frozen toy contract stipulates that check X is decisive, and therefore stipulates that Y has zero marginal value after X. The held-out cases reuse that exact transition rule. This checks harness accounting and demonstrates why an independently sampled transition corpus and calibration protocol are necessary; it does not satisfy #5306's held-out residual gate.

## Preserved construction failures

1. First replay failed before producing rows: a `correlated` metadata flag was unpacked as a three-field check record (`TypeError: cannot unpack non-iterable int object`). No scientific allocation was consumed. The parser was corrected to exclude metadata from feasible checks.
2. First auditor run failed because it invoked the replay module through a subprocess that still failed on the same type error. Its empty output is not treated as evidence.
3. The initial auditor shared the candidate's chooser/reducer functions, violating independence. That audit was rejected and replaced with separately implemented expected policy, reducer, loss and accounting rules. The retained final audit reports zero discrepancies.

## Limits / next evidence

No runtime, verifier, GUI, model, latency, population, or production claim. The T0 scientific gate remains **UNMET**: no external or independently generated held-out transitions; the VOI cost table is an authored constant, not calibrated; candidate-vs-selective advantage is not independently identified. Any further result requires a new immutable allocation and a genuinely independent held-out transition set. The stale shared clone/fetch contention is recorded on Issue #5306; this package is created through GitHub API as an additive path and does not modify that worktree.
