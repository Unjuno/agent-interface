# Real-container autoresearch: directional transfer and scorer freshness

Decision: **reject a universal fixed-direction motor policy; retain an explicit evaluator-refresh integration candidate.** Issue #121.

Publication base: `e31ce43995f399555bba40ed6efe9840c7fdf983`. Immutable executed runtime: `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`. Existing runtime, workflow and historical results are unchanged.

## Actual execution and conditions

33 fresh real ViZDoom/X11 comparison sessions were completed: 18 directional comparisons, 9 mirrored-policy successor trials, and 6 matched scorer-refresh trials. Two short X11 preflights, two OS-input fixture-construction sessions and one no-input engine calibration are excluded. One failed X11 bootstrap is preserved. No model calls or set_action/make_action policy input occurred. The refresh candidate explicitly requests advance_action(1, True) for evaluation; it is not claimed non-perturbing.

The initially missing engine was restored through GitHub MCP artifact 10398313098. Its archive SHA-256 is `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`; all 2592 source entries and 12 wheel hashes passed. A missing inherited Xauthority path caused the first bootstrap failure; an explicit empty experiment bootstrap file fixed it without runtime changes.

| Condition | Value |
|---|---|
| CPU / affinity | Intel Xeon Platinum 8272CL, nominal 2.60 GHz / CPUs 0-4 |
| Frequency | Not pinned; shared-host load uncontrolled |
| OS / Python | Linux 6.18.44 x86_64 / CPython 3.13.5 |
| Engine | ViZDoom 1.3.0, Freedoom MAP01, skill 1, ASYNC_SPECTATOR, 35 tics/s |
| Rendering / input | Visible 640x480 game, private 1280x800x24 Xvfb/Openbox, XTEST |
| Libraries | Pillow 12.3.0, NumPy 2.3.5 |
| Input path | Retained session_map01_v13/v12, Executor, InputOwner |
| Authority | 3075 ms from runtime clock; 5000 ms requested hold; expected expired terminal |
| Initial states | Original threat-contact-v2 plus actual a/d 650 ms hold, 350 ms coast, saved through OS-only setup |
| Repeats | Three restores per cell; save carries RNG state, not independent worlds |

Freeze receipts precede measurement: Stage 1 `84594dcd...`; Stage 2 `4d5ced7d...`; Stage 3 `eb735bc2...`. Stage 1 randomizes state order and alternates policy order, not full counterbalancing. Stage 2 is sequential exploration without contemporaneous attack controls. Stage 3 order is passive/refresh, refresh/passive, passive/refresh. No consumed live case was rerun.

## 1. Directional transfer failed

Exact bindings: space=attack, s=back, a/d=left/right strafe. Arrow-key turning is not strafing. The prior compact report did not retain an exact candidate key list; this tests the explicit program, not a strict reproduction of an ambiguously named historical primitive.

| Saved state | Attack: space | Back-left: s,a,space | Back-right: s,d,space |
|---|---:|---:|---:|
| Original | 0/3 kills | 3/3 kills | 0/3 kills |
| Left-shifted | 3/3 kills | 0/3 kills | 0/3 kills |
| Right-shifted | 3/3 kills | 0/3 kills | 3/3 kills |

Left-shifted attack ended at health 12 from 97 in all three cases. All other cells ended at 97. The HUD value 12 was checked against the actual PNG. These policy cells used 7-8 rounds. No deaths or map exits occurred. Reversing direction moved the successful region instead of creating a universal primitive. Kills alone would hide the 85-point health loss. Stage 2 is not a paired causal comparison with Stage 1.

Correction to prior interpretation: observed 2/3, 2/3, 1/3 success counts at increasing durations do not themselves disprove monotonicity of the underlying success probability. Retain the counts, not that stronger statistical assertion. Current 3/3 cells are not reliability guarantees either.

## 2. Getter consistency was not freshness

All positive scorer events in the 27 directional sessions were recorded only after the input deadline. That alone would not prove stale state, so an independent no-input real-engine calibration followed. Episode and state tic remained 1 after 200 ms sleep, advance_action(0, True), and another 200 ms sleep; a one-tic refresh returned tic 17.

This configuration therefore cannot treat a new getter acquisition timestamp as proof of fresh engine state. Repeatedly reading the same cached tic can pass a same-tic coherence check. Final outcome values can still be correct while their time-local progress interpretation is invalid. The calibration's acquisition bracket covers get_state only, not its full field set; the refresh duration was separately timed.

## 3. Matched evaluator-refresh repair

The versioned trace_session.py adapter keeps the OS program and owner deadline unchanged. Both arms sample at 10 Hz and record the same additional engine-tic/health/timing fields. Only refresh1 requests advance_action(1, True) before the scorer getter set, on the owner thread. It never selects engine buttons and writes the extra state only to evaluator files. Historical 35 Hz passive runs are not the matched comparator.

| Endpoint | Passive getters, 10 Hz | One-tic refresh, 10 Hz |
|---|---:|---:|
| Final independent kill result | 3/3 | 3/3 |
| Positive event observed before authority deadline | 0/3 | 3/3 |
| Distinct source tics before deadline, each case | 1, 1, 1 | 31, 31, 31 |
| First positive after first admission, median | 3139.285 ms | 2197.909 ms |
| Same metric range | 3105.256-3269.059 ms | 2194.902-2991.059 ms |
| Verified release / terminal agreement | 3/3 / 3/3 | 3/3 / 3/3 |
| Missed sampling periods | 0 | 0 |

This is improved observability, **not evidence of killing faster**. Refresh changes workload and may perturb asynchronous scheduling; it does not expose the exact engine event time. Refresh calls cost median 30.980 ms, range 15.709-46.840 ms. Blindly calling this at 35 Hz could overrun the period or starve commands. The tested 10 Hz cadence has only six-session evidence.

## Verification and residual issue

All 33 comparison sessions have exact declared key admission, matching accepted program SHA/intent/deadline, expected expiry, independently verified empty input, strict five-field final scorer equality, and unchanged runtime-source hashes. Privileged score fields are absent from controller events before finish.

Deadline-to-verified-empty: median **0.960 ms**, range **0.578-4.363 ms**, 33 cases. These are observed values, not real-time upper bounds. First-admission-to-empty is only an interrupted-occupancy upper bound.

Scorer missed periods total: Stage 1 **16**, Stage 2 **4**, Stage 3 **0**. Misses were descriptive in the frozen plan; no zero-miss claim is made for all 33.

Independent replay checks all 33 results, **507 exact PNG observation hashes**, typed/full-frame identity, fixture saves, runtime sources, action identity, release causes, and **199 full diagnostic acquisition brackets**. Twelve prefreeze tests plus twelve post-hoc corruption tests pass. One offline image-audit invocation exceeded the tool's 45-second call limit; the read-only audit was subsequently completed, not a live rerun.

**Not fixed:** all 33 inherited direct_final_sample receipts still create a zero-width timestamp bracket after obtaining the payload. The payload timestamp lies outside it. This is counted, not silently repaired. The 199 valid brackets belong to the new diagnostic wrapper, not that inherited sink. Final value equality passes, but production integration must repair the old receipt separately.

## Generality and next question

Retain exact action identity, bounded authority, and provider-specific freshness evidence separating source generation from acquisition time. Do not install a fixed Doom direction as a generic interface policy. An advancing engine tic is useful here; a static document's unchanged version is not automatically stale. Provider semantics matter.

Next: bind the final scorer value to an honest full acquisition bracket and reduce the measured refresh cost without leaking scorer data into policy. Then test observable-state-conditioned primitive selection without fixture-ID or privileged-score shortcuts. This work does not validate that selector, arbitrary GUI applications, navigation or frontier-planner efficacy.

Related disciplines: control systems (authority vs utility), distributed systems (freshness vs coherent cached reads), and measurement science (observer intervention/event-time uncertainty).

## H / T / D / C / U

H: local primitive superiority can fail transfer; explicit source refresh can restore progress observability.
T: three hash-frozen finite stages, 33 real X11 sessions, retained construction/calibration outcomes, independent replay and 24 tests.
D: reject universal fixed direction; retain 10 Hz refresh only as an evaluator integration candidate. Residual final-receipt defect and unquantified observation perturbation block production claims.
C: geometry, save-restored RNG, async scheduling, late effects, costly refresh and provider-specific source clocks.
U: three local states, three repeats/cell, one host, no model/planner, no exits. No population confidence interval, combined uncertainty or coverage factor is justified.

Time differences use the same runtime monotonic clock. Nanoseconds divided by 1000000 give milliseconds. The reported 1 ns clock resolution is not accuracy; health/ammo/kills are dimensionless game counts, not physical units.

## Retention / replay

Full raw ZIP is a conversation artifact, not uploaded to GitHub or Actions. GitHub retains source, freeze receipts, compact results, report and archive digest. The archive contains the recorded runtime-source closure for replay, not a complete engine distribution. In a separate extracted workspace, run `python research/doom/autoresearch_direction_v1/audit.py . --out replay.json`; Pillow is required for pixels, or use --no-pixels. The tests require retained preflight evidence. A fresh live run requires the full pinned bundle, fresh output IDs and a newly frozen relocated plan. Do not overwrite a normal checkout's product runtime directory or rerun consumed allocations.
