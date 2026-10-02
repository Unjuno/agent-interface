# Host boundary result (not the formal container run)

Allocation source: `1ecc98b03ed5efeaee2cb664feb6f5e91280389f`; frozen source and ledger identities are in `FREEZE.json` and `SHA256SUMS`.

## Executed

- Construction: `python3 -W error::ResourceWarning -m unittest -v` — 8/8 passed.
- Syntax: `python3 -m py_compile candidate.py audit.py test_bounds.py` — passed.
- Candidate boundary run: `python3 candidate.py ledger.json results/host-boundary-01/raw.json` — exit 0; one 10-row cohort, all 8 unresolved-outcome completions emitted.
- Separate raw-only audit: `python3 audit.py ledger.json results/host-boundary-01/raw.json` — exit 0; `PASS_BOUNDS_SCOPED`, `errors=[]`.
- `git diff --check` — passed.

## Observed result

`N=10, S=6, F=1, M=3`; observed-only rate `6/7` would promote at `3/4`; assigning every unresolved outcome to failure gives `6/10` and does not promote; no-assumption sharp interval is `[3/5, 9/10]`, so the threshold decision is `PROMOTION_UNIDENTIFIED`. All eight completions were enumerated, both endpoints attained, and the independent auditor rejected denominator drop, outcome relabel, duplicate episode identity, boolean threshold, and duplicate completion corruption.

Raw SHA-256: `0f428c7d3da7b29cb982d1d7502536c3f562e569d6e16d18e4e7d37f5e1ed4ec`. Candidate stdout SHA-256: `d9d71397f7212f61941cba33cbe3ea7bd31d0cb19b799deb645f87e3a15bed04`. Auditor stdout SHA-256: `00cd1f13ba775126aecbab7cc90ac8adf8f1dd062c8a11c7bcf44277095e5e6c`.

## Boundary

This is an executed CPython 3.14.5/macOS arm64 host boundary experiment, not Docker evidence. The previous shared Docker allocation was consumed at a conflicting preflight STOP. No container, image, GUI, model, empirical benchmark cohort, or external effect is part of this result. A fresh exclusive OrbStack allocation is required for the identical frozen candidate/ledger/auditor to establish container portability. The synthetic result does not establish a real cohort promotion decision, sampling uncertainty, generalization, or benchmark qualification.
