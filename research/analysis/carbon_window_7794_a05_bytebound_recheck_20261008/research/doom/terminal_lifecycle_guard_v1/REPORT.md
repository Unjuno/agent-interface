# Real MAP01: task end, input authority, and late admission

Decision: **PASS for the tested cooperative-provider lifecycle guard; no general visual-control or gameplay claim.** Issue #173.

Publication base `7f42fd577dff98d6a27a8eceb79d86bee0358bf9`. The executed runtime remains immutable `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`, restored from artifact 10398313098. The archive digest `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`, all 2592 source entries and 12 wheels were verified locally. No historical runtime, workflow or result was edited. No model call or engine button-selection API was used.

## Discovery, then one-variable comparison

The previous restored-timeout experiment established a false-success classification but used no held input. This successor asks a different question: does an ended task automatically end an otherwise-valid action lease?

One excluded 250 ms setup case passed. Two baseline discovery cases were frozen at `3407a837e3ad3260b233717db62e50e83df222e3`. In the 40-second timeout case, independent X11 samples still showed keys held 2275.006 ms after the first terminal observation; owner-verified empty arrived after 2275.912 ms and a fresh late input was accepted. The 60-second control remained running. These discovery cases are not pooled into the matched estimates.

The observed boundary justified an explicit terminal-lifecycle latch. The 12-case comparison, source hashes and thresholds were frozen at `638959d51e7393a5cfc81ea0ea08c025028964f7` before the first measured case. Each of three blocks restores the same saved state into four sessions: 40-second and 60-second episode limits, each with the guard disabled and enabled. Order alternates as recorded in matched-plan.json; it is not a full randomization over worlds.

Both arms request exactly `[a,d]` for 5000 ms, with an unchanged owner deadline 3075 ms from a runtime clock receipt. After the primary program closes and the original deadline plus 150 ms passes, the driver tries one fresh-sequence, new-ID `[a,d]` 50 ms hold. Here fresh submission means a new ID and the latest available observation sequence, not an extra image capture at late-submit time. All arms use the same refreshed 10 Hz evaluator and a separate read-only X11 connection sampling the physical keymap at nominal 100 Hz. The opposed chord provides real input without selecting a combat policy.

## Additional capability, not hidden gameplay assistance

The guard receives ONLY a trusted provider-local session epoch, ordered sequence, terminal Boolean and acquisition timestamp. In this experiment the provider derives the Boolean from the ViZDoom episode state. This is additional application information, **not inferred from pixels and not an unchanged screenshot-only gameplay protocol**. Kill count, health, ammunition and success/failure classification are not used to choose or revoke an action.

The latch moves from open to ended once. Under the existing Executor RLock, it latches before cancelling the matching active intent through the existing cancel channel. Future submissions check that same latch under the same lock. Duplicate end receipts cannot issue another cancellation; old/foreign epochs cannot cancel the current one. The gate cannot extend a deadline, issue a new action, reopen an epoch, or declare task success. It does not authenticate malicious providers. A new session requires a new gate.

The unguarded baseline still satisfies its original deadline contract. Its continuation after episode end is not an authority bypass under that old contract; it exposes the absence of an explicit task-lifetime condition. Adding this condition is a capability change, not a neutral measurement change.

## Actual results

All 12 matched cases completed once without a rerun.

| Condition | Primary result | Late input admitted | Observed-end to owner-verified empty, median [range] |
|---|---|---:|---:|
| Timeout, unguarded | expired 3/3 | 3/3 | 2275.470 [2160.797, 2275.775] ms |
| Timeout, guarded | cancelled 3/3 | 0/3 | 0.991 [0.615, 1.361] ms |
| Still running, unguarded | expired 3/3 | 3/3 | not applicable |
| Still running, guarded | expired 3/3 | 3/3 | not applicable |

Within-block reduction in the post-observation interval: median **2274.414 ms**, range **2159.806-2274.854 ms**, three pairs. This is not a task-completion speedup, a reaction time from the true engine event, or a real-time upper bound.

The baseline timeout cases contain **651 actual post-end key-down samples** on the independent connection. The guarded cases contain no such sampled down state, but polling can miss intervals shorter than its period: zero sampled-down records is NOT a proof of zero physical duration. The separate owner verification establishes the reported empty-state endpoint. No continuous-occupancy reconstruction is claimed.

All three guarded timeout cases have exactly one matched cancellation and no fresh late admission. All six running-control sessions complete the late 50 ms chord, with two actual key admissions each. The initial primary chord also has two exact admissions in every case. The control condition therefore does not merely stop all operations to obtain apparent safety.

### The false-success defect is deliberately NOT hidden

In all six timeout cases, historical score.json still declares map_exit=true and one_life_map_exit=true while the refreshed independent samples report episode_finished=true, timeout_reached=true and map_exit=false. Thus **six strict full-score comparisons remain FAIL**. All six running cases agree. The lifecycle guard neither uses nor fixes that classification. These original files are retained unchanged, and no gameplay success is claimed.

## Environment and measurement conditions

| Condition | Value |
|---|---|
| Host CPU / affinity | AMD EPYC 9V74 80-Core Processor / logical CPUs 0-4 |
| Clock / batch | frequency unpinned; shared-host load unknown; one session at a time |
| Python / kernel | CPython 3.13.5 / Linux 6.18.44 x86_64 |
| Engine / scenario | ViZDoom 1.3.0, Freedoom MAP01, skill 1, ASYNC_SPECTATOR, 35 tics/s |
| Display | private Xvfb/Openbox 1280x800x24; visible 640x480 game |
| Key input | existing XTEST / Executor / InputOwner, [a,d] |
| Evaluator | owner-main-thread one-tic refresh at 10 Hz, honest acquisition brackets |
| Independent input observer | separate X11 connection and thread, query_keymap, nominal 10 ms wait |
| Python dependencies | Pillow 12.3.0, NumPy 2.5.3, python-xlib 0.33; full pip inventory retained |
| Sample size | three restores per cell; same saved RNG, not independent maps |

One-tic refresh is an evaluator intervention with wall-time cost, not a free/non-perturbing read. The timer starts at a completed acquisition, not the unobserved engine transition. The timeout occurs before the 3075 ms authority deadline in all intended cases. The saved source tic is 1366, already about 39 seconds into the episode. The 40/60-second distinction is a test condition, not a runtime guard heuristic.

## Verification

- 37 premeasurement tests pass: 19 lifecycle tests (including eight simultaneous duplicate deliveries) and 18 acquisition tests.
- 11 post-hoc retained-file tests pass, including 10 mutations of clocks, keymaps, release, identity, program hash and timeout evidence: **48 tests total**.
- Independent full replay rederives all 12 results, 417 acquisition brackets, 3950 keymap samples and the paired interval reduction.
- 321 exact full-observation PNG/RGB hashes and typed/full capture identities are checked.
- All 12 primary releases and nine admitted late actions have verified empty terminal receipts. No orphaned engine/Xvfb/Openbox process remains.
- Zero scorer period misses and zero top-level prefinish kill/death/timeout field leakage were detected. The allowed lifecycle bit affects cancellation/rejection by design; this is not complete information-flow isolation.
- 1176 evidence-manifest entries verify, including the excluded discovery/setup cases, exact historical source closure and fixture saves.

The frozen audit.py is unchanged after measurement. Post-hoc replay/tests are separately labelled. Full replay is a second implementation of numerical/classification checks on the same retained data, not a new experiment. A correctly formatted record or hash is not proof against a malicious writer replacing an entire dataset.

## Measurement variables and units

| Name | Meaning | SI / stored unit | Definition / assumptions | Type |
|---|---|---|---|---|
| accepted_ns | input program admission time | s / integer ns | existing Executor monotonic clock | nonnegative integer scalar |
| valid_until_ns | hard authority deadline | s / integer ns | unchanged runtime-clock receipt plus 3075 ms | integer scalar |
| finished_ns | end of terminal-state acquisition | s / integer ns | after provider getter set; not the engine event time | integer scalar |
| verified_ns | owner-confirmed empty state | s / integer ns | lease-bound release cause with keys/buttons empty | integer scalar |
| keymap started_ns/finished_ns | independent query envelope | s / integer ns | ordered read on its own X11 connection | integer scalar pair |
| sequence | provider sample sequence | 1 | monotonically increasing inside one session | nonnegative integer scalar |
| epoch / intent_token | session / action identity | 1 | opaque local identifiers; no time unit | strings |
| bitmap | physical X11 key bits | 1 | 32 integer bytes; keycode bits independently decoded | integer vector |
| ended | provider lifecycle condition | 1 | exact Boolean; neither success nor cause | Boolean scalar |

Unit check: subtract only endpoints on the same host CLOCK_MONOTONIC timeline, then divide integer ns by 1,000,000 for ms. The provider's 35-Hz tick is a separate clock and is NOT substituted for wall time. Negative deadline-to-empty in guarded cases means early cancellation, not negative reaction time. No combined u_c or coverage factor k is estimated; empirical ranges and sampling limits are reported.

## H / T / D / C / U

**H:** an explicit, trusted episode-end invalidation can promptly revoke the matching input lease and block fresh submissions without suppressing running-session actions.

**T:** two baseline discovery sessions; freeze 12 matched sessions; retain all first outcomes, 48 tests and independent keymap/source/pixel replay. One setup preflight is excluded.

**D:** the frozen scoped integration gate passes: 3/3 timeout cancellations within 50 ms of observed end, zero late timeout admissions, normal running behavior 6/6, valid acquisitions and verified release. General visual semantics and shared-runtime promotion remain HOLD. The old score classifier still fails 6/6 timeout cases.

**C:** the gain is primarily earlier authority revocation because of extra lifecycle evidence. It is not a better game policy or a faster image pipeline. Unknown/provider-lost signals, true deaths/map exits, multiple active epochs, display disconnects and event-delivery loss are not live-tested here.

**U:** one saved state, three pairs, shared host, 10 Hz evaluator and 100 Hz sampled keymap, observer cost, and additional cooperative information. These limit generalization and prevent continuous-occupancy or hard-real-time claims.

Related fields: capability-based control (revocation without new grants), distributed systems (epoch-bound terminal events), and measurement science (source event versus observation and release clocks).

## Next discriminator

Test loss/staleness of the provider terminal signal while the existing owner deadline remains the backstop. Do not infer terminal status from a frozen screenshot, empty response or elapsed control time. A production integration must separately fix timeout success classification and verify its own signal provenance.

## Retention

GitHub retains the code, both freeze receipts, full plans, compact results and raw selected endpoints. The complete raw evidence.tar.xz is supplied in the conversation ZIP, not uploaded to GitHub/Actions; archive.json pins its length and SHA-256. README documents replay and reconstruction of a fresh environment. Do not rerun consumed output IDs or overwrite historical runtime files.
