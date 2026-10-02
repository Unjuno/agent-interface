# Issue #6435 T0 — deadline/slack measurement method

## Result

`METHOD_PASS_SCOPED`. The independently implemented raw-only auditor exactly reconstructed all 32 deadline-ledger rows, the six route-choice pair dispositions, and both route-surface patterns. All four preregistered corruptions were rejected during construction. This validates only that this finite method distinguishes its stipulated controls; it does **not** test whether any model changes proposals under urgency.

## Frozen question and H / T / D / C / U

- **H:** The finite protocol distinguishes slack-invariant feasibility from real deadline-sensitive feasibility while retaining all outcomes and effect-based timing; it can identify a seeded rank reversal without calling the null an interaction.
- **T:** Six route-choice pairs (12 cards): two valid slack-equivalent controls, verification-crosses-deadline false-equivalence, lease-expiry mismatch, changed-intent mismatch, and a true slack-sensitive positive control. Separately, eight outcome cards at no-deadline/5/7/20 cutoffs (32 offered trials) and two route panels (16 trials) exercise all-attempt curves, a planted rank reversal, and a no-interaction null.
- **D:** Exact raw reconstruction, all-attempt denominators, common phase-clock integrity, effect-not-proposal correctness, six expected classifications, YIELD when mandatory verification cannot fit, correct reversal/null detection, and rejection of four frozen corruptions.
- **C:** Utilities, route bounds, and truth labels are stipulated; the fixture may be too simple to represent prompt framing, model drift, selection, or genuine response-time behavior.
- **U:** No model, human, GUI, real clock, actual effect, causal deadline effect, safety guarantee, or human-tempo claim. T1 is required to test the substantive behavioral hypothesis.

## Formal execution evidence

- Candidate invocation: exactly once. Separate raw-only auditor: exactly once after candidate exit 0. Retries: 0.
- Runtime: OrbStack Docker, Linux/arm64, image `python:3.12-slim`, image ID `sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; network disabled, 1 CPU, 256 MiB, 64 PIDs, read-only container root, all capabilities dropped, no-new-privileges.
- Raw candidate output: `run/candidate.json`. Independent verdict and summary: `run/audit.json`. Execution timestamps and runtime ID are in `run/`; `run/SHA256SUMS` binds retained formal artifacts.
- Candidate source, auditor, fixture, preregistration and runner match `FREEZE.sha256`.
- Frozen main intake: `eacb1346866f660d9d34eb36cd9691fd8184e5ff`; Issue body SHA-256: `1595973b983c2ed86cc316ddd57e68e081b203d3423c572e6a66fe4079fbce96`.

## Reproduction

From repository root: `sh research/analysis/deadline_slack_equivalence_6435_t0_v1/RUN.sh`. The script verifies the local pinned image ID and refuses to overwrite existing formal outputs. It runs one candidate and one separate auditor.
