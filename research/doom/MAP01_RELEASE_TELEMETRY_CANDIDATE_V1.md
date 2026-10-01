# MAP01 release telemetry candidate v1

Status: **RETAINED CONSTRUCTION — telemetry primitive PASS; MAP01 integration UNCERTAIN.**

Base commit: `f678afa8eb7b1db1da7cfd9a15ff65d4c146d74d` (`Retain held-input telemetry source closure`).

Task: `O3-G1-RELEASE-TELEMETRY-CANDIDATE-001`.

This change implements only the measurement repair requested by the retained source closure. It does **not** change the v39 controller, cover policy, hold duration semantics, lease semantics, or retained allocations, and it makes no new model call. The working container has no `vizdoom` package, so no fresh MAP01 episode is represented here.

## Increment beyond the retained source closure

The retained evidence already establishes that ordinary `InputOwner v10` key-up has no symmetric timestamp and that requested `duration_ms` can understate owner-commanded hold time. The smallest missing primitive is therefore a timestamped explicit release edge.

`input_transition_owner_v1.py` wraps the unchanged `input_owner_v10.InputOwner` instead of editing the historical owner. For explicit `up` / `button_up` it:

1. takes a caller timestamp immediately before the existing owner call;
2. enqueues the unchanged v10 release without any pre-release `input_state` query;
3. takes a caller timestamp immediately after v10 returns — v10 returns after its X11 `d.sync()` when it owns the input;
4. only then samples owner state;
5. emits `input_release_transition` with owner/intent identity and the bounded release window.

The **absence of a pre-release state probe is deliberate**. Sampling the owner before releasing would add a queue round trip while input remains held and would make the instrument alter the quantity it is intended to measure.

`doom_retained_input_backend_v1.py` is a typed-DOOM adapter candidate. It fails closed unless the backend believed the key was owned before release and the post-release owner-owned count matches the expected count. This catches stale/backend-owner disagreement instead of relabelling it as valid telemetry.

`analyze_map01_direct_retained_input_v1.py` accepts only matched `input_admission` + verified `input_release_transition` pairs carrying the same intent token/key. Current-schema proxy-only traces remain `measurement_ready=false`.

## Container validation

Compilation passed for all seven candidate/test source files. **10/10 unit tests passed**:

- wrapper semantics: 4/4;
- DOOM adapter fail-closed ownership checks: 3/3;
- direct retained-input analyzer: 3/3.

A finite Xvfb experiment then exercised the release timing primitive with an exclusive X11 owner thread and caller→queue→owner→`d.sync()` architecture. Every trial pressed one key, verified it physically down via `XQueryKeymap`, bracketed the queued release with **no pre-release state observation**, then verified the key physically up.

Measurement conditions: Python 3.13.5, Linux 6.18.44 x86-64 / glibc 2.41, AMD EPYC 9V74, process affinity 5 vCPUs, Xvfb 800×600×24, 500 trials.

| Metric | Result |
|---|---:|
| physical down verified | 500 / 500 |
| physical up verified | 500 / 500 |
| release caller-bracket minimum | 33.471 µs |
| median | 35.309 µs |
| p95 | 60.087 µs |
| p99 | 133.485 µs |
| maximum | 220.112 µs |

These values validate the **X11/queue bracketing primitive in this container**. They are not MAP01 runtime latency, not a hard real-time bound, and not a claim about v10 under capture/model workload. The retained completed-hold censoring was approximately 10–18 ms in the immediately preceding source-closure work; this candidate is designed to replace that structural censoring with a direct edge, but the amount of narrowing under MAP01 load remains unmeasured.

## H / T / D / C / U

**H — falsifiable hypothesis.** A separately versioned release telemetry layer can expose a bounded normal key-up edge without adding a pre-release observation round trip or changing controller policy semantics.

**T — minimum validation.** Compile candidate sources; unit-test token propagation, no-pre-release sampling, ownership mismatch rejection, and analyzer fail-closed behavior; then execute 500 queued X11 press/release trials with physical keymap verification.

**D — decision.** **PASS** for construction and X11 queued-release primitive. **UNCERTAIN** for MAP01 runtime integration because this container lacks VizDoom. Therefore **FAIL to authorize a recovery-vs-coast policy experiment yet**; that comparison remains blocked until a provenance-complete MAP01 session emits and audits the new transition on real normal holds.

**C — competing explanations / ways this can break.** Scheduler load may widen the caller bracket; an asynchronous expiry/focus release can make a later explicit `up` stale; pointer paths have different ownership shape; a post-release owner sample can delay downstream feedback even though it no longer extends the hold; Xvfb queue timing may not represent the WSL/VizDoom runtime.

**U — uncertainty.** Dominant remaining uncertainty is integration, not the direct X11 primitive: exact queue/scheduler behavior under MAP01 capture load, complete source/provenance closure, interaction with asynchronous owner release, and whether every ordinary hold produces one matched release transition. No combined uncertainty or coverage factor is justified before that live validation.

## Next gate

Create a provenance-complete MAP01 session version selecting this adapter and including both telemetry sources in `sources.json`; freeze it before allocation. Run **one no-retry telemetry validation**, not a recovery-policy efficacy run. PASS requires every admitted normal hold to have one verified direct release transition with matching intent/key, all input empty at terminal, unchanged independent task scoring behavior, and no missing/duplicate transitions. Only after that gate should bounded recovery be compared with coast on retained-input occupancy plus independently useful task feedback.

## Related domains

- **Real-time/control systems:** separates policy semantics from actuator-release observability and exposes scheduler-dependent jitter instead of hiding it in requested durations.
- **Measurement science:** removes observer-induced hold extension and preserves interval/bounded evidence rather than substituting proxy timestamps.
- **Human–computer interaction / embodied agents:** enables fair comparison of useful retained control during model latency rather than comparing nominal action programs.

Machine-readable result: `research/doom/results/map01-release-telemetry-candidate-v1/analysis.json`.
