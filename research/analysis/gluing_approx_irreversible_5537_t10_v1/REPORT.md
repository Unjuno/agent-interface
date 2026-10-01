# Issue #5537 T10 — typed approximate-admission boundary

**Disposition: `PASS_APPROXIMATE_IRREVERSIBLE_GATE_SCOPED` for the frozen finite model.** The matrix includes true beyond-tolerance rows, explicitly distinguishes all three contracts, and the independent raw-only bitmask oracle agrees on all 180 records. All six mutation controls were demonstrated non-identity and rejected.

## H / T / D / C / U

- **H:** Approximate evidence may be accepted only under the declared action contract; irreversible admission requires explicit opt-in, and evidence beyond tolerance must never admit.
- **T:** Five frozen evidence fixtures × four tolerances × three contracts × three action classes = 180 rows. Candidate enumerated all eight binary assignments; separate auditor used bitmask relation intersection. Host-local CPython 3.14.5/macOS arm64; no container lease, GUI, model, network, or external effect.
- **D:** Runner exit 0. Auditor exit 0; `base_errors=[]`; 6/6 non-identity mutation controls rejected. Exact sections admit all action classes. `exact_only` rejects all approximate rows. `reversible_approximate` admits reversible/compensable and refuses irreversible. Explicit opt-in admits approximate irreversible only when spread ≤ tolerance. Nine true beyond-tolerance rows (spread 0.5, tolerance 0.25) all refuse. Empty and incomplete cases refuse. Analysis index refreshed and checked: 237 retained-result directories.
- **C:** Hand-authored finite binary relations and scalar tolerance. Contract labels are assumed typed inputs, not authenticated runtime authorization.
- **U:** No calibrated real-interface tolerance, general sheaf solver, freshness/provenance, live GUI/model/task effect, empirical safety, production correctness, or cross-domain claim.

## Reproduction and identities

- Freeze base: `bbb3676bf7c05b9e16f3bf98a9a2ff8f63df0693`.
- Candidate command: `python3 -B run_experiment.py`, one invocation, exit 0, 180 rows.
- Raw SHA-256: `1ccfdd7451167421c4978b3090bc0a5511b430fac01146324e4823f60cb6c89e`.
- Independent command: `python3 -B audit_raw.py`, one invocation, exit 0, `PASS_APPROXIMATE_IRREVERSIBLE_GATE_SCOPED`.
- Audit JSON SHA-256: `5695ba823039d159db843207f0e900da48ecec4d3ee5281ae514743acbb117d7`.
- Candidate SHA-256: `2ff34c41561664f877cd8ef0d65891f87cd4f4cc73cd1379bb387522bbe43b81`.
- Runner SHA-256: `234298dadda620b415b8bf3ad2de4850f883599b34df660b2849da22b7958365`.
- Auditor SHA-256: `f68b409991df3402e45deff8c7a77792669d3e6dc0f86484a8cccbcee305e740`.
- Construction: 6/6 unit tests; py_compile passed before freeze. Repository `git diff --check` passes.

This PASS is a finite synthetic decision-boundary result only. T5–T9 are preserved unchanged; T9 remains `HOLD_SCOPE_GAP` and is not retroactively upgraded.
