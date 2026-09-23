# Local real-MAP01 interruption matrix

Status: **PASS for the five-case development matrix; no recovery-policy efficacy claim.**

Issue #88. Immutable runtime base: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`.
V2 plan and executed-source hashes were committed before allocation at
`56eeda0dd3368c24bb4589d547489bbfbf6c1b69`. This lane changes no historical runtime,
retained allocation or formal recovery-v2 experiment.

## Actual execution

GitHub packaging-only run `34973453255` exported fixed source and binary wheels;
it ran no GUI/model experiment. Artifact `10398313098` was retrieved through GitHub
MCP and its archive, 2,592 source entries and 12 wheels passed hash checks. The
experiment then ran real ViZDoom **inside the local disposable container**, not on
a surrogate game or a newly dispatched MAP01 workflow.

Conditions: CPython 3.13.5, Linux 6.18.44 x86_64/glibc 2.41, Intel Xeon Platinum
8573C, five-CPU affinity, uncontrolled shared-host frequency, Pillow 12.3.0,
NumPy 2.2.4, ViZDoom 1.3.0, isolated Xvfb 1280x800x24/Openbox, visible game 640x480,
ASYNC_SPECTATOR/35 tics per second, skill 1, seed 990616, threat-contact-v2 fixture.
IWAD SHA-256 matches `a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b`.
CLOCK_MONOTONIC reports 1 ns resolution; that is not accuracy. One fresh session
per case, five total; zero external model calls.

## Code and measurement repair

The previous development-v2 analyzer returns a ready zero-hold result if release
rows are absent, even when an acknowledged down remains. This exact negative
control is retained in `missing_release_counterexample.json`. It does not invalidate
dev-02's observed normal one-key result, which did contain its release.

The new `occupancy.py` joins id-less down records by accepted intent token, pairs
repeated keys in order, rejects missing/duplicate/inverted normal release evidence,
clips to a measured window and takes the **union** of simultaneous key intervals.
It is integrated into `run_matrix.py`/`run_matrix_v2.py`, not merely proposed.
Interrupted cleanup rows are censored rather than promoted to exact release edges.

## Results

Each row is one observation, not a timing distribution. The window is the measured
accepted-to-terminal program lifetime, **not actual frontier-planner waiting time**.

| Case | Requested operation | Measured window, ms | Any-key occupancy bounds, ms | Terminal |
|---|---|---:|---:|---|
| Coast | no input, 300 ms | 476.772 | 0.000 | completed |
| Single | a, 240 ms | 446.196 | 343.958-344.591 | completed |
| Chord | a+d, 240 ms | 460.054 | 349.744-350.232 | completed |
| Cancel | a+d, 2000 ms; cancel 120 ms after held receipt | 162.737 | 0.000-126.021 | cancelled |
| Expire | a+d, 2000 ms; 500 ms absolute lease | 529.598 | 0.000-497.056 | expired |

The last two zero lower bounds mean no positive duration is certified by this
conservative reconstruction, **not no input**. Both have two down acknowledgements
and a matched independently verified empty-input cause. Simultaneous keys count
once, never as the sum of their individual hold durations.

Cancel-request to verified empty: **3.812971 ms**. Deadline to verified empty:
**0.477331 ms**. Each is one sample, not an upper bound or real-time guarantee.
Physical release preceded terminal by 35.747670 ms and 31.573745 ms respectively.

All five primary programs verified empty keys/buttons. All **5/5 submissions using
the old initial observation sequence were rejected** before new admission. All
five final independent scorer samples agreed with the established terminal score
on all five fields; no scorer-only event appeared in the complete runtime/delivered
streams. All scores were zero kills, zero deaths and no exit: no gameplay advantage.
The cancellation was timer-triggered, not a natural health-guard efficacy test.

Coast missed **one scorer period**; the other four missed zero. Cadence was explicitly
descriptive in the committed plan, not relaxed after the result. Zero missed periods
or a new useful-control benefit must not be claimed.

## Why the interval construction is bounded

| Field | Meaning | SI / stored unit | Definition/domain | Type |
|---|---|---|---|---|
| admitted_ns | down admission boundary | s / ns | before owner XTest down; nonnegative same-runtime clock | integer scalar |
| input_ack_ns | acknowledged down | s / ns | after owner X11 sync; not before admission | integer scalar |
| release_call_started_ns | up request boundary | s / ns | before unchanged v10 queued up | integer scalar |
| release_call_returned_ns | up completion boundary | s / ns | after v10 up/sync return | integer scalar |
| verified_ns | independently checked empty state | s / ns | matching lease/cause release boundary | integer scalar |
| window_start_ns, window_end_ns | accounting boundaries | s / ns | ordered same-clock timestamps | integer scalars |

For ordinary input, down lies inside its admission/ack bracket and up inside its
caller bracket. Under the frozen single-owner source and no unrecorded external
input, ack-to-up-request is contained in the commanded hold; admission-to-up-return
contains it. Intersecting each with the same measured window preserves containment.
Taking unions preserves it again and avoids overlapping-key double counting. The
union sweep adds only the portion after its already-covered right endpoint. The
complement within the fixed window reverses the occupancy bounds to obtain no-input
bounds. Timestamp differences remain ns; division by 1,000,000 yields ms. A synthetic
two-key test yields a 61 ns union lower bound, not a 120 ns summed duration.

After interruption, a later explicit cleanup does not prove continued occupancy
until its request. The lower interval is therefore empty and the upper interval
ends at the earliest applicable verified-empty/cleanup boundary. This is intentional
loss of precision. Completed input lacking normal release evidence fails instead
of becoming coast. The runner separately checks planned admission counts. Complete
append-order traces are assumed; this is not a proof against arbitrary log forgery,
wholesale deletion or unrecorded external input. Normal owner bookkeeping is not
continuous physical-keymap observation.

## Validation and failure retention

**20/20 new tests and 34/34 existing regressions pass.** Two new property tests each
contain 5,000 trials: a discrete union oracle and interval inclusion. Deleting release
rows from the real new chord trace is rejected. A one-byte archive mutation is
rejected. The full archive audit verifies 122 manifest entries, all numerical timing,
scorer agreement, runtime-source closure and executed/published source hashes.
The archive digest covers the manifest itself. Five Python Git blob identities were
compared with the local tested/executed bytes before publication.

V1 failed on missing Pillow before any GUI case. It remains failed and was not
reused. V2 checks real runtime imports before allocation creation, preserving the
same run_case, seed, fixture, case order, gates and occupancy code. V2 then ran once
and completed the entire matrix. See `failed_v1.json`, `plan.json`, `plan_v2.json`.

## Retained artifact and replay

GitHub retains sources, frozen plans, result and archive digest. The complete
**6,752,991-byte** `map01_container_interruption_evidence.zip` is delivered in the
originating conversation. It contains raw logs, scorer states, PNG/AIT images,
environment, failed-v1 evidence and source files. It is **not uploaded into GitHub
or Actions**. SHA-256:
`d57149b64f916bb960d84080e7ef67598ca23db15a601425e5294a783ae9c9c8`.

```sh
python research/doom/container_interruption_v1/test_occupancy.py
python research/doom/container_interruption_v1/audit_archive.py /path/to/map01_container_interruption_evidence.zip
```

Replay is offline and needs only Python's standard library. Do not rerun consumed
allocation IDs; new live work requires a new plan/ID.

## H / T / D / C / U

**H:** the unchanged real v13 stack preserves release/scorer/stale-sequence contracts
under normal, cancelled and expired input, while windowed analysis distinguishes
missing/censored evidence from zero occupancy.

**T:** the frozen five fresh threat-fixture sessions, 54 regressions, retained-file
replay and negative controls. Stop at the first case failure, no same-allocation retry.

**D:** scoped development PASS 5/5, with one descriptive scorer-period miss. Real
planner latency, natural health-guard behavior and recovery efficacy remain unproven.

**C:** synchronous snapshots in the historical hold loop can delay ordinary up.
The measured 240 ms requests lasted about 344-350 ms, consistent with that path,
but capture/encode/scheduler contributions were not causally isolated. Longer input
can be useless or harmful.

**U:** asynchronous censoring, shared-host scheduling, observer overhead, one sample
per condition and absent useful outcomes dominate. No statistical confidence interval
or combined uncertainty is justified.

Next, integrate this measured-window union API with actual planner start/return clocks
and independently useful outcomes. Do not substitute nominal hold duration for an
owner-enforced deadline, and do not count cancelled/censored input as zero.

Related fields: control systems (authority versus lifecycle), measurement science
(censoring/observer effects), and distributed systems (immutable evidence/one-shot
allocation ownership).
