# Post-hoc review correction — 2026-10-05

The formal one-shot result and its raw outputs remain unchanged. Two review findings are recorded here as append-only qualifications:

1. The frozen `clairvoyant_lower_bound` DP initialized each tick's next-state map by copying every prior state. This admitted a zero-cost idle transition not available to candidate/baseline simulators. The reported zero lower bounds are invalid and are withdrawn; they were diagnostic only and did not participate in candidate-vs-baseline, completion, calibration, or mutation gates. No corrected oracle optimum is claimed.
2. The published formal candidate is compressed to preserve the 314,596,618-byte raw without pushing that raw blob. Therefore the frozen `python3 audit.py` command expects a materialized file not present in a fresh checkout and would also overwrite the committed formal audit outputs. Do not rerun it on a checkout containing the frozen receipts. `replay_audit.py` is a separate, read-only supplemental validator: it reads `candidate.json.gz` directly, verifies the original raw hash and frozen source/input identities, reconstructs the candidate/baseline rows, and writes only a new `formal_01/replay_validation.json`. This supplemental check does not alter the original candidate/auditor invocation counts or formal disposition.

The audit source itself remains byte-for-byte frozen at the hash in `FREEZE.json`. The official disposition remains `FAIL_UNSAFE_RESUME`, based on reversed-cohort noncompletion and unmet informative benefit gates, independently of the withdrawn oracle diagnostic.

The official result summary's phrase “144 reversed episodes” is clarified: these are **144 episode×cost rows** (24 distinct reversed held-out streams evaluated in six checkpoint/replay cost cells), not 144 unique streams. All 144 rows were incomplete.
