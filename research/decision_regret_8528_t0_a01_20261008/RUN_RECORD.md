# Formal run record — Issue #8528 T0 A01

## Freeze and environment

- Corrected preregistration commit: `b423c53b87530eaa798355a96fd441088af5ad4f`.
- Superseded source-only freeze retained as ancestor: `353ce273ad26f61866ffcdd9f8c1eb403f57d50f`; correction and reason are in `FREEZE_AMENDMENT.md`.
- Before formal commands: all ten frozen source files were checked locally using Git blob hashing against GitHub readbacks; all hashes matched. Formal candidate and auditor counters were both 0/1.
- Execution date: 2026-10-08. Python 3.12.10; Microsoft Windows NT 10.0.26200.0; PowerShell 7.6.6. The commands ran directly in the current local workspace. No Docker or WSL boundary was needed or started for this deterministic finite computation.
- No external network, model, GUI, human, game, agent runtime, or input was used by either formal command.

## Exact formal commands and retained stdout

1. `python -B candidate.py --dir .` — exit 0; stdout in `CANDIDATE.stdout.txt`; one invocation. Raw output: `candidate.json` (22 rows across 8 cases).
2. `python -B audit.py --dir .` — exit 0; stdout in `AUDIT.stdout.txt`; one invocation. Independent result: `PASS_METHOD_SCOPED`, zero errors, all 7/7 mutations rejected; full report in `AUDIT.json`.

No retries or reruns of either formal command occurred. The independent audit implementation does not import or execute the candidate module; it reconstructs expected output rows from visible inputs and independently enumerates the supplied audit-only truth/loss.

## Results

- Primary stable case: evidence ages `[3,4,5]`; age-only sum 12; toy unsafe-exposure duration 0; integrated toy regret 0.
- Primary changed-truth case: identical candidate-visible decision rows and the same evidence ages `[3,4,5]`; age-only sum 12; toy unsafe-exposure duration 0; integrated toy regret 3.
- Fresh misleading control: age 0, regret 1.
- No-open-opportunity control: `NOT_APPLICABLE`; no regret scalar and age-only sum null.
- Changing admissible set control: regret 2, computed against the same per-tick admissible set.
- Hard-safety control: expected `FAIL_HARD_SAFETY`, no regret scalar; one planted safety event remains a separate hard result, not a utility tradeoff.
- Unidentified observation-use control: regret 0 in the fixture but causal attribution `NOT_IDENTIFIED`.
- Unknown truth/incomparable clock: `UNKNOWN`, no numeric regret or age-only scalar.
- Overall `PASS_METHOD_SCOPED` means only that this finite arithmetic/boundary method test and its exact audit gates passed. The toy unit loss is not human/task utility; no causal benefit, real-world safety, user outcome, product improvement, or applied validity is established.

Construction suites were run again after recording the formal result: candidate tests 3/3 passed; independent audit tests 8/8 passed. These tests are construction/verification checks and do not increment the frozen formal command counts.
