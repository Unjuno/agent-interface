# A05 byte-bound replay result

## Decision

**A05 decision: `PASS_BYTEBOUND_REPLAY_SCOPED`.** The one-shot candidate and auditor completed successfully and reconstructed all ten frozen cases. The auditor's raw JSON status is `PASS_DIAGNOSTIC_SCOPED`. The first nine cases agree between the global-lexicographic and serial-ASAP comparators; the discriminator has two feasible schedules, global `A=1,B=0`, while serial-ASAP is infeasible. There were zero A02 differences and no auditor errors.

## Reproducibility and custody

The four execution inputs (fixture, candidate, auditor, construction test) were reconstructed from the exact checked-in A04 Git blob bytes plus exactly one final LF byte, reproducing their A04 manifest SHA-256 values. A05 recorded those reconstructed bytes and its own Git blob IDs before execution. Post-run source hashes still match the freeze. The old A04 candidate and audit semantic content match this A05 replay.

## Limits and disposition

This is a finite synthetic comparator-method diagnostic, run once on native Windows Python 3.12.10 using only the standard library. No Docker, WSLc, or WSL execution occurred; this is not migration evidence. It establishes no operational scheduler, energy, emissions, or CO2 claim.

The A04 `FREEZE.json` and `PREREGISTRATION.md` manifest discrepancies remain unresolved. A05 does not modify, replace, or retroactively validate A04, and does not justify merging or revising predecessor PR #8183. Retain the A04 artifacts unchanged. A05 is a successor record for deciding whether a separately frozen/reviewed diagnostic can be integrated.

## Raw evidence

- `formal_a04/candidate.json` — candidate output.
- `formal_a04/audit.json` — auditor output.
- `formal_a04/candidate.stderr.txt` and `formal_a04/auditor.stderr.txt` — empty stderr captures.
- `RUN.json` — exact invocations, exits, environment, source hashes, and output hashes.
- `FREEZE_A05.json` and `PROTOCOL_A05.md` — pre-run source custody and protocol; preserved unchanged.
