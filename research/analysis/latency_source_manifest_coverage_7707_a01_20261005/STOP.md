# A01 terminal infrastructure stop — Issue #7707

**Disposition: `STOP_INFRA`.** The single frozen WSLc candidate launch request ended without an observable candidate artifact. The `wslc.exe run` client session returned terminal exit code 1 with no stdout/stderr; its Windows process disappeared, `CANDIDATE.json` was absent, and the designated output directory was empty. The exact failure cause is unknown.

## Evidence

- Frozen launch: `wslc.exe run --rm --pull never --network none --cpus 1 --memory 512M --name codex-7707-manifest-a01-candidate`, pinned cached image and read-only `/src` plus separate `/out` as specified in `FREEZE.md`.
- The launch had remained live in WSLc for repeated observations; a read-only WSL process snapshot showed its client sleeping in `poll_schedule_timeout`, with no candidate Python process visible in that WSL process list.
- On 2026-10-04 18:25:43 UTC / 2026-10-05 03:25:43 Asia/Tokyo, the same session ended with exit code 1 and no output. Windows process 29480 was absent; no `CANDIDATE.json` existed and the output directory was empty.
- The separate earlier read-only `wslc.exe list --all --format json` session also ended with exit code 1 and no output.
- `wslc.exe --version` (`3.0.1.0`) and `run --help` had returned successfully. This proves the CLI frontend responds, not that the container service ran the candidate.

## Invocation ledger and classification

- Candidate launch requests submitted: 1.
- Candidate script execution/result: **unobservable**; no script exit status or raw result exists. Do not claim candidate count 0 or 1.
- Independent auditor invocations: 0 (the frozen protocol requires a confirmed candidate exit 0 first).
- Retries/replacement allocations: 0; do not retry this consumed one-shot allocation.
- Scientific result: none. This is `STOP_INFRA`, not `FAIL_METHOD`, hypothesis evidence, or proof that a functioning container cannot run the study.

The frozen source/input/main identities and decision gates remain unchanged. This terminal receipt supplements the pending launch-status comment on Issue #7707; it does not alter prior #7501 T0/A01/A02 evidence.
