# #6969: derived acquisition responds to modeled cue phase

Outcome: **PASS_METHOD_SCOPED; HOLD_LIVE_TRANSFER**. Formal allocation 02 ran on
2026-10-03 09:06:21–09:06:23 UTC in three sequential private OrbStack containers.
Candidate, four-input legacy diagnostic and independent auditor each ran once,
all exit 0, no OOM/restarts. No formal rerun or post-result scientific changes.
Zero live effect and authority events. This is not an actual latency benchmark.

## What was tested and found

All 147 source-derived rows matched the independent integer-set oracle: 134
timing cells and 13 boundary/negative controls. Ten frozen copied-output
corruptions were all rejected; full mutant copies are retained. Candidate source
mount contained only candidate.py and source-only fixture.json, not the oracle,
labels or supplied acquisition/downstream events.

| Matched contrast | First interval | Second interval | Generated result |
|---|---|---|---|
| Onset-only, expiry fixed; latency 1/1/0 | [9,20] | [11,20] | capture [10], eligible_effect_in_model vs capture [], not_acquired |
| Duration fixed at 2ms; latency 0/0/0 | [9,11] | [11,13] | capture [10], eligible_effect_in_model vs capture [], not_acquired |

The onset-only pair holds all source protocol fields fixed except case identity
and onset. Its changed interval duration is explicit; the second pair addresses
phase translation at fixed duration with its separately frozen zero latencies.

The four-input diagnostic against byte-pinned original A04 source confirms that
changing only onset (9->11 in c01; 11->9 in c02), while supplied memberships and
downstream events remain fixed, leaves both classify tuples unchanged: two
eligible_effect tuples and two not_acquired tuples. This confirms the specific
onset-insensitivity of that classifier; it does not falsify its original
snapshot-consistency PASS. Predecessor #6803 sources and raw evidence are unchanged.

Boundary counts: 76 eligible_effect_in_model, 22 not_acquired, 41
delivered_no_decision, 2 acquired_not_delivered, 2 decision_no_effect,
3 UNKNOWN and 1 NOT_APPLICABLE. These are authored finite cells, not samples or
an empirical success rate. For the 134-cell grid alone: 73 eligible, 40
delivered_no_decision, 21 not_acquired. The expiry-51 cases with onset 11..50
capture at 50, deliver at 51 but decide at 52; this explains all 40 grid failures.

## Preserved infrastructure failure and custody

Allocation 01 stopped before staging at the private Docker socket permission
check; formal candidate/probe/auditor invocations were 0/0/0. Original freeze and
sources are preserved at `82100b79c845db3200d9637e070f6bde86db8832`, with
FREEZE.json and PREFLIGHT_01.md. No occupied raw output was replaced.
Allocation 02 was prospectively frozen at
`4b3da15ca4dbb4720e173475174c3a6c77169176` and published in Issue #6969 comment
5967501728 before formal execution. Only Docker administration uses explicit
guest root; every scientific container still ran as 501:501.

Cached arm64 Python image digest:
`sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`.
Observed inside all three containers: memory.max 536870912 and cpu.max
100000 100000 (512MiB/one CPU). Inspect confirms network none, read-only root,
cap-drop ALL, no-new-privileges, separate read-only input custody and writable
role-specific output. The current VM-root cgroup read was max/max, so no
independent VM-wide hard resource cap is claimed.

The initial standard Git invocation was blocked by the Xcode license shim; the
existing CommandLineTools Git worked without accepting/changing the license.
The first push waited on osxkeychain and was terminated before delivery; the
already authenticated gh credential helper completed the push. No secret was
stored in this package. These infrastructure incidents did not execute/tune the
scientific candidate or auditor.

## Verification and interpretation boundaries

Construction: 12 tests first failed for absent implementations, then all passed
before freeze. Two additional post-run runtime/custody tests first failed for an
absent verifier, then passed; all 14 package tests pass. This suite is separate
from formal invocations and exercises the pure model locally. The verification
skill requires read-only evidence checks before PASS/integration claims.

Exact source and raw custody is in FREEZE_02.json, STAGING_02.json, formal_02/,
RUN.json and MANIFEST_SHA256.json. verify_evidence.py checks every package file,
the preserved original Git freeze, unchanged scientific hashes, exact command
arrays, observed container limits, independently reconstructed raw/audit data
and all retained mutation copies. The dedicated CI workflow performs these
checks without launching another formal container allocation.

The model declares closed intervals, synchronized integer clocks and deterministic
downstream latency. Timely decision may produce effect after expiry but before
horizon: control-late-effect observes time 22 after expiry 20. Effect tokens are
simulated strings, not verified application receipts. Native capture availability,
rendering/delivery jitter, GUI/effect transfer and clock semantics remain untested.
No model quality, actual task effect, O3/O4, economics, real-time DOOM, human-tempo
or product/safety conclusion follows. #59/#57 and repository roadmap stay open.

## Integration handoff

Merge the evidence package and its CI through a reviewed PR, preserving the
source-freeze commits. Do not run runner.py execute again: allocation 02 is
consumed. A future native/live experiment requires a separate preregistration,
owned eligible runtime, independent source-bound effect oracle and new paths.
The experimental worktree was merged with main through `66822a57d` after the
formal run without altering the scientific package. This keeps frozen commits
reachable rather than rewriting them by rebasing.

The complete existing Analysis Index Python matrix was executed locally: 25/26
commands exit 0. The #6590 T1 geometry-feasibility command has two failures:
`test_geometry.GeometryFeasibilityTests.test_freeze_sidecar_sources_and_known_result_are_bound`
and `test_runner.RecoveryRunnerTests.test_recovery_freeze_hashes_all_sources_and_stop_provenance`.
Both compare the current workflow SHA256 5804f307... with frozen b19000e0....
The workflow's preceding pinned-source restore step was intentionally NOT
reproduced by overwriting the current checkout. All failure output is retained
in local_ci/07.stderr.log and LOCAL_CI.json. These tests are not reported as
locally passing; the actual Actions job performs its restore step separately.
Only actual PR check results can confirm that workflow gate.
