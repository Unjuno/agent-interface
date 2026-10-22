# Current-main native WSL/Xvfb standard-caller generation/recovery run

This packet re-runs the repository's live-Xvfb standard-caller integration on the current local main checkout `e7d79d04de46202622873bf116adb909abb0dee2`. The prior retained native-WSL result used source `108b271...`; this fresh run tests the current source, not a replay under the prior commit.

The frozen test composes guarded input, process/window generation identity, one injected post-press acknowledgement fault and one failed automatic release, bounded recovery, stale alias refusal, fresh generation observation, independently read task effect and final input readback. The runtime task-success field must stay null. Full conditions and source hashes are in `CONDITIONS.json`; raw stdout, report, observation image, environment and Xvfb lifecycle are under `public-evidence/raw/r02/`.

## r02 result

`r02` completed one current-source standard-caller test and passed all 13 independent report checks. Recovery completed in **10.246 ms** with release independently verified; a separate X client read the recovery key up. The stale alias was refused before dispatch, and a fresh generation continuation changed the independently read application property to `[3]`; key press/release and close-time empty key/button state were independently observed. The recovery and continuation effect latencies were **34.508 ms** and **36.559 ms**. Runtime `task_success` remained null. Xvfb PID 453 was absent after cleanup. The report, screenshot, stdout, environment, and auditor output are retained under `public-evidence/raw/r02/`.

`r01` stopped before the integration test because WSL could not resolve the worktree's Windows-absolute `.git` pointer. Its exact prelaunch error is preserved and was not retried. `r02` fixed only the source-provenance check by verifying frozen source SHA-256 values before the run; it did not change product code or test behavior.

This uses the already-running native Ubuntu WSL distribution and one private Xvfb display with a pinned Python venv. It does not use WSLc, Docker, an external model, a physical desktop, or shared GUI. The test and audit are one-trial scoped evidence, not MAP01 or population reliability. Do not rerun or overwrite `r01`; any follow-up needs a new run ID and a new conditions file. Recheck the published `r02` copy with `python public-evidence/raw/r02/audit_raw.py` from the repository root.

## Attempts

`r01` stopped before Xvfb/test entry because native WSL could not resolve this Windows worktree Git pointer; see `public-evidence/raw/prelaunch-failure-r01.txt`. It is a launcher STOP, not an experimental result, and was not rerun. `r02` has a fresh run ID and source SHA256 verification independent of Git metadata; its frozen inputs are `CONDITIONS-r02.json`. The scoped result is current-main synthetic caller evidence, not live physical desktop qualification.
## Shared evidence copy

The local `raw/` tree retains the original unredacted records and is intentionally excluded from publication. `public-evidence/` contains text-only redacted copies, the publication redaction record, and a separate `SHA256SUMS`. Only local checkout/user-profile/cache paths and the local host name were replaced; measured values, statuses, timings, request records, and synthetic images are unchanged. Recheck the published `r02` copy with `python public-evidence/raw/r02/audit_raw.py` from the repository root.
