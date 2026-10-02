# One-shot run protocol

Allocation: `ADOPTION-CONDITIONED-RECOURSE-6358-T0-HOST-20261002-01`  
Base main: `44416db9decb5182b8119591580fc2a652b8cebb`  
Branch: `research/adoption-conditioned-recourse-6358-t0-20261002`

## Preflight

1. Confirm fresh GitHub main is still the frozen SHA. If advanced, fast-forward and refreeze before running any formal command.
2. Recompute every source hash in `FREEZE.json`; validate JSON, run construction unit tests and `git diff --check`.
3. Confirm `results/formal-01/` is absent and no branch, PR, or parallel owner now targets this exact issue/path/allocation.
4. This synthetic CPU-only T0 needs no shared GPU/WSLc/container allocation. It must make no runtime or causal-effect claim.

## Formal commands (once only)

Run exactly once and preserve stdout/stderr/exit:

```powershell
python -B candidate.py --cases cases.json --out results/formal-01/candidate.raw.json
```

Only if candidate exits 0, launch one separate process for the independent raw auditor:

```powershell
python -B auditor.py --cases cases.json --candidate results/formal-01/candidate.raw.json --out results/formal-01/audit.raw.json
```

Candidate failure, timeout, audit failure, or malformed output is retained; no retry, fixture edit, seed substitution or tuning.

## Frozen interpretation

`PASS_METHOD_SCOPED` means only the deterministic finite ledger and auditor match the frozen schedules, not that a recovery policy causes a general improvement. Required primary result is generic/witness/public-stagger/placebo 2/4 versus recipient-specific routing 4/4, with wording placebo route/outcome identical to generic and both declared recipient classes at 2/2. Every case/policy retains all offers and independently audited receipts/capacity/deadlines. Otherwise preserve the exact FAIL/HOLD/STOP. General policy effects remain unverified and require multiple isolated, reset, policy-assigned cohort windows with carryover audit.
