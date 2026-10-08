# T0 finite-model result — Issue #5305

## Outcome

`PASS_T0_FINITE_MODEL` for the explicitly frozen five-atom, 31-subset model
only. The initial independent audit invocation exposed an incorrect expected
aggregate in the audit code (`STOP_AUDIT_EXPECTATION_MISMATCH`); the exact first
candidate raw remains unchanged. A corrected, separate raw-only audit then
matched all 31 candidate rows to a separately implemented oracle and rejected
all four mutation controls.

## Findings

- Candidate projection counts: `CONFLICT=14`, `PASS=14`, `FAIL=2`,
  `UNCERTAIN=1`.
- The intentionally lossy ternary reducer projected all 14 fresh-conflict
  cases to `UNCERTAIN`, so it erased the conflict-vs-ignorance distinction in
  every conflict-containing subset in this model.
- Exact duplicate atoms `s1`/`s1dup` in the same declared independence group
  contributed one support group, not two.
- Stale-only evidence projected to `UNCERTAIN`; fresh support/refutation to
  `CONFLICT`; stale evidence did not erase fresh evidence.
- Corruption controls: candidate sign, freshness count, duplicate grouping and
  conflict projection — rejected 4/4.

This is a finite contract discriminator, not evidence of GUI safety, fewer
retries, calibrated belief masses, verifier quality, runtime benefit, or
improved action admission. Independence and freshness are trusted fixture
metadata; the model has one proposition and only five atoms.

## Provenance

- Base main: `02bff58173426efc2288bd375f283a6500f80784`
- Python: 3.11.9, standard library only
- Candidate raw SHA-256: `1b59434596847c7ee39de96c7845ee96e02f683325506b41cabf212e7a932f12`
- Audit JSON SHA-256: `c304b2242c2b9cd021a9572055bc09a3623668c86e5532ca5d1ee18d389abd0`
- Candidate source SHA-256: see `FREEZE.json` (captured after the single candidate invocation).
- Auditor source SHA-256 is retained in `FREEZE.json`.
- The candidate and audit experiment used no Docker, network, model, GUI, action,
  GPU, CUDA, or external service. GitHub MCP was used afterward to publish the
  retained evidence. This was an exhaustive finite model check, not a hardware
  experiment.
- No source/main files or predecessor artifacts were changed.

## Delivery limitation

The original checkout could not materialize a fresh worktree because disk
space ran out while checking out retained raw assets. To avoid changing or
deleting existing local artifacts, the evidence was delivered additively via
GitHub Git Data API on a fresh branch based on current main. The PR remains the
review/integration gate; no merge is claimed here.
