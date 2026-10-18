# A02 outcome: audit method failure; allocation consumed

Frozen source commit: `dd198fcc0acc8e94d7473b5530d5764f323e0eb2`.

The candidate/runner executed once and produced 61,800 deep-attempt rows across 103 synthetic worlds and three arms. The independent auditor executed once and exited 1 at `sentinel_not_reproducible`, before any scientific decision gate. Static diagnosis found that the runner used its world-generation RNG after prior draws, while the auditor recreated a fresh RNG and sampled from the final eligible list. The sentinel contract therefore was not independently reconstructible as coded.

A02 is consumed. Do not rerun or repair its output under this allocation ID. The first audit stdout/exit and candidate inputs/outputs are retained byte-for-byte in `raw/` as deterministic gzip streams; `UNCOMPRESSED-SHA256.txt` records the original JSON byte hashes. Mutation controls were not run because the main audit did not pass. This is `HOLD_AUDITOR_METHOD_FAILURE`, not a scientific PASS or FAIL.

SHA-256:

- `shallow-input.json.gz`: uncompressed SHA-256 is in `raw/UNCOMPRESSED-SHA256.txt`.
- `candidate-allocation.json.gz`: uncompressed SHA-256 is in `raw/UNCOMPRESSED-SHA256.txt`.
- `candidate-output.json.gz`: uncompressed SHA-256 is in `raw/UNCOMPRESSED-SHA256.txt`.
- `audit-first-output.txt`: `de2fdfd06c3f54bec7775a6b4c873632ef99263298da60c556bb8a067ea334ac`
- `audit-first-exit-code.txt`: `4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865`

Scope remains offline synthetic method testing only.
