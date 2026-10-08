# Issue #5537 T10 — explicit contracts and true beyond-tolerance coverage

## H / T / D / C / U

**H.** The action gate should distinguish three typed contracts: `exact_only` denies every approximate section; `reversible_approximate` permits only reversible/compensable approximate work; and `explicit_allow_approximate_irreversible` additionally permits approximate irreversible work. Every case with spread above tolerance must be rejected independently of contract/action class.

**T.** Fresh-main, new allocation and path. Enumerate five evidence fixtures (exact, within tolerance, beyond tolerance, no global section, missing context), tolerances `{0, 0.25, 0.5, 1.0}`, three contracts, and three actions = 180 rows. Fixed positive spread is 0.5, so tolerance 0.25 is a genuine beyond-tolerance point. Candidate enumerates all eight binary assignments. Independent bitmask oracle reconstructs nested decision inputs/outputs. Six corruption controls use nested fields and exact pre/post values; pre-formal construction tests assert matrix semantics including `spread=0.5 > tolerance=0.25`, and every control's non-identity before audit.

**D.** Scoped PASS iff 180/180 rows match independent oracle; exact accepts all actions; exact_only rejects approximate for all actions; reversible_approximate admits reversible/compensable but rejects irreversible; explicit opt-in admits approximate irreversible only when `spread <= tolerance`; all contracts/actions reject true beyond-tolerance, empty, and incomplete cases; and all 6 non-identity mutations are rejected. Unsafe admission is FAIL; missing row/semantic coverage or audit mismatch is STOP/HOLD.

**C.** Hand-authored binary relations and scalar tolerance; contract identity is a synthetic typed assumption, not authentication or calibrated policy.

**U.** No general sheaf solver, empirical interface tolerance, live evidence, GUI/model, task effect, runtime/production safety, or population claim. T5–T9 raw and audit artifacts remain immutable.

## Freeze protocol

- Freeze current main: `bbb3676bf7c05b9e16f3bf98a9a2ff8f63df0693`.
- Allocation: `gluing-approx-irreversible-5537-t10-20261001-01`.
- New path: `research/analysis/gluing_approx_irreversible_5537_t10_v1/`.
- CPython 3.14.5/macOS arm64; host-local because no exact resource lease is assigned. No shared Docker inspection/use.
- Run construction tests before freeze. Freeze hashes. One candidate invocation and one separate auditor only after exit 0; no retries or post-freeze source/raw edits.
