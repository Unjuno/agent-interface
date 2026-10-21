# Isolated prestarted-supervisor Xvfb run 39620589667

## Frozen execution

- GitHub Actions run: `39620589667`; isolated job: `prestarted-cancel-xvfb`.
- PR #9315 head: `a44f940105c94f2efb8b59decfa8d8ca442ab4cb`.
- The receipt's `GITHUB_SHA` is `eddf7f14f7833f130c8cdf85ab74e4e4c9ffd32b`, the workflow merge ref, not the PR head.
- Ubuntu 26.04, Python 3.12.15, Xvfb 2:21.1.22-1ubuntu1.3.
- The run's downloaded artifacts, including the raw receipt, observation image, Xvfb log, and sibling job packets, are retained byte-for-byte in this directory. `SHA256SUMS` covers each retained file except the README and manifest themselves.

## Outcome

The public caller reached the supervisor path, but the cleanup request was rejected before the XRes disconnect check or release. The returned diagnostic is `invalid_fields: ["owner_generation.child_pid"]`. The admission record captured session `ae8582431a4e4f8ea7935e9215bc150c`, child PID 2680, resource base 6291456, and binding revision 0. The retired-owner obligation snapshot still contained key `a` (keycode 38); the child exited with code -15. The cancellation transaction completed in 20.255458 ms as `UNKNOWN`, with `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`. Independent release readback and task oracle are null. Do not interpret the later harness close/readback as supervisor release evidence.

The sibling `x11-integration` job passed. Its outputs are preserved separately under the sibling artifact directories here; they do not alter the failure or supply the missing supervisor release/task oracle.

## Diagnosis and next discriminator

The failed field indicates that the adapter constructed the request's generation PID from the refreshed owner snapshot after cancellation had retired the child. That snapshot can omit the process record even though the owning parent still retains the actual `Process.pid`. The local source patch now obtains one PID from the parent-owned process and uses it for both `owner_pid` and `owner_generation.child_pid`; the regression fixture intentionally supplies a stale cached PID and omits the process map. This diagnosis is not considered fixed until the focused test passes in normal and optimized Python and a new isolated Xvfb composition validates the request and reports its subsequent XRes, release, readback, and task-effect stages independently.

This is a consumed first outcome. Keep it distinct from runs 39617200853, 39618514760, 39619576394, 39620085797, and later attempts. It is not WSLc, MAP01, blocked-server release, task-success, reliability, or matched-efficiency evidence.
