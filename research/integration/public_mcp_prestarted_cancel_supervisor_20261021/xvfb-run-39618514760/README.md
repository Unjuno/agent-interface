# Isolated prestarted-supervisor Xvfb run 39618514760

## Frozen execution

- GitHub Actions run 39618514760, job `prestarted-cancel-xvfb`, PR #9315.
- PR head/source commit: `29ef64690d641ba71b531bb5c571555728ea4339`.
- Raw receipt `GITHUB_SHA`: `480214ca08970ff680cc01171d9289f9568c8195` (the pull-request workflow merge ref, distinct from the PR head).
- Ubuntu 26.04 runner, Python 3.12.15, Xvfb 2:21.1.22-1ubuntu1.3. Xvfb log is empty.
- `raw.json`, `observation.png`, and `xvfb.log` are copied byte-for-byte from the uploaded artifact.
- SHA-256: raw JSON `0664cb95bcc8e0ee2ecb99db2e13692bd72270a74d031eb14f85f25f8d92230e`; observation PNG `751e00d5f926a15128a45baec1b2310aabee740b363119bd79dd224986d81f01`; Xvfb log `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

## Outcome

The first harness defect is fixed: the public MCP cancellation reached the real owner method, retired the blocked owner process (exit `-15`), and returned in 13.055 ms. The new failure is inside the supervisor request contract. The supervisor worker returned `unknown / invalid_cleanup_request`; no XRes disconnect check or release/readback completed. The public result remained `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`. `independent_release_readback`, `late_request_horizon_readback`, and `independent_task_oracle` are null. Later test cleanup observed `a` and `b` up, but that is not attributable to the supervisor and does not pass the scenario.

The trace preserves the values available outside the process: owner PID 2721, XRes base 6291456, session ID `3e5e9393ff994670aa24bd8d21d0b6b5`, binding revision 0, and obligation `{keys: {a: 38}, buttons: []}`. The current worker validator rejects a request when any required field/type or generation equality fails, but its result collapses all such cases to `invalid_cleanup_request`; the exact rejected predicate is not present in this raw receipt. Add field-level rejection evidence before another live attempt so the next outcome can discriminate a contract mismatch from an X-server behavior issue.

## Scope

This is a failed real-Xvfb composed attempt that did exercise the public owner cancellation and prestarted supervisor, but it did not reach server disconnect or release. It does not establish release, task effect, recovery, reliability, WSLc, MAP01, or efficiency. Preserve this first outcome unchanged.
