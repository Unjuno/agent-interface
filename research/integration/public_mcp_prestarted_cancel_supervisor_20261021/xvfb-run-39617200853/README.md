# Isolated prestarted-supervisor Xvfb run 39617200853

## Frozen execution

- GitHub Actions run 39617200853, job `prestarted-cancel-xvfb`, on PR #9315.
- Workflow head recorded by GitHub: `8f8e9990971bee92f42c3448052ec2f9430ff8d3`.
- Raw receipt's `GITHUB_SHA`: `08af29b16194b5c1310aceb25c2182290febe764` (discrepancy retained; the receipt is not rewritten).
- Ubuntu runner, Python 3.12.15, Xvfb 2:21.1.22-1ubuntu1.3, X server PID 2738.
- Frozen conditions and raw outputs are in `raw.json`, `observation.png`, and `xvfb.log`; these are copied byte-for-byte from the uploaded artifact. The Xvfb log is empty.
- SHA-256: raw JSON `46b8ede05e488aa8016381172a5e610f9b14f341b05d8f1b95dc5048cda79bb0`; observation PNG `751e00d5f926a15128a45baec1b2310aabee740b363119bd79dd224986d81f01`; Xvfb log is empty.

## Outcome

The run is a harness failure, not a supervisor behavior result. The cancellation registry invoked the traced `OwnedGuardedSessionOwner.cancel_guarded` with `operation_id` and `deadline_monotonic_ns`. The test wrapper still accepted only `(owned, token)`, raising `TypeError` before it could call the real owner method. The receipt records a 3.206 ms cancel response, `cancel_unconfirmed`, `cleanup_status=UNKNOWN`, `release_confirmed=false`, `task_success=null`, and `replay_allowed=false`. No cancel-entry trace, independent release readback, late-request horizon readback, or independent task oracle was obtained. The public call remained pending during the bounded cleanup wait; close returned `busy`. The final harness cleanup later observed both keys up, which is not attributable to the supervisor and is not a passing result.

The first outcome is retained and must not be overwritten or rerun under this run ID. The test wrapper was corrected separately to accept and forward the two keyword arguments. That source repair is not evidence that the Xvfb scenario passes; only a distinct subsequent execution can establish that.

## Scope

This run does not qualify input release, supervisor correctness, task effect, bounded recovery, reliability, WSLc, MAP01, or efficiency. It did use private Xvfb for one attempt, but failed before the supervisor's cancellation path was exercised. The raw receipt's source SHA differs from the GitHub run head SHA; preserve both values pending provenance diagnosis.
