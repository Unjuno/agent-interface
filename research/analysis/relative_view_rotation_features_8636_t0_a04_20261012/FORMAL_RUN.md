# A04 formal execution record

## Pre-run state

- Allocation: `UNJUNO-8636-ROTATION-FEATURES-T0-A04-20261012`.
- Frozen base main: `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
- Frozen source commit: record before formal execution.
- Candidate invocations: 0/1. Auditor invocations: 0/1. Retries: 0/0.
- Output path: `results/a04-outcome/` (must be absent or empty).
- Exact executable, commands, seeds, and source hashes: `FREEZE.json`.
- Predecessors A01/A02/A03 remain unchanged; no prior formal data will be rerun.
- No WSLc, Docker, GUI, model, OS input, network, or external application will be used.

This file records each formal invocation once: exact command, UTC start/end, stdout/stderr, exit code, raw file count/bytes, and archive hash. An unknown status is HOLD; do not reissue.

## Formal execution record (append-only)

The pre-run freeze was committed as `2f15e4f9a68cea4b9e47940b8f9b468ba5dd07cf` on branch `research/8636-rotation-features-t0-a04-20261012`, with base `main` SHA `f185a9059d485a4f8d5a65e9e7f6782897f67eae`. Candidate and auditor were each invoked once, with no retries.

| Role | Start UTC | End UTC | Exit | stdout / stderr | Outcome |
|---|---|---|---:|---|---|
| Candidate | 2026-10-12T02:18:47.2531656Z | 2026-10-12T02:18:55.3904552Z | 0 | `A04-candidate.stdout.txt` / `A04-candidate.stderr.txt` | 360 trials; 2,198 raw files; 62,552,757 bytes |
| Independent auditor | 2026-10-12T02:19:19.9697971Z | 2026-10-12T02:19:32.5028000Z | 1 | `A04-auditor.stdout.txt` / `A04-auditor.stderr.txt` | First mismatch: oracle arm yields on near-singular image-detection failure, contrary to auditor's no-yield assumption; no summary |

The raw output was archived as `A04-first-outcome.tar.gz` (335,880 bytes; SHA-256 `631b987c8184f2fd75be32fb06f9acee9ae59a504cdd441e3fbdb1508d9e945e`) with per-file manifest `A04-raw-manifest.json` (SHA-256 `7c75014da1f1581461381238d6c93178bfbf395391874b49aeb032670cf68a6f`). A read-only post-run check matched all 2,198 archived regular files to the manifest; no missing, extra, or mismatched entries. The failed audit is preserved as `HOLD_UNCERTAIN`; no candidate or auditor rerun was attempted.

See `A04-RESULT.md` for the exact first failure, interpretation limit, and actionable harness finding.
