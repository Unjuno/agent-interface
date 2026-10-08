# Issue #6617 T0 — revision-timed cutover finite event model

## H / T / D / C / U

**H.** On the single frozen stable-turn schedule, version-bound read-only preparation will reduce logical ticks from committed final request to verified intended effect versus final-only preparation, while safe-arm consequential inputs remain bound to the exact authenticated committed version on every revision/authority boundary.

**T.** One deterministic no-model finite event simulation; 10 scripted cases × 3 arms (30 traces): final-only, deliberately unsafe naive provisional effect, and version-bound read-only preparation. The cases are stable request, negation/cancel, changed recipient, quotation, two-speaker turn switch, stale preparation completion after revision, stop before input, stop after accepted input with unknown effect, stop after independently verified irreversible effect, and urgent physical release while planner work is pending. Time is integer logical ticks, never wall-clock. A separate raw-only auditor hardcodes the truth table and independently reconstructs admitted inputs, verified effects, latency, stale-epoch rejection, pending/irreversible stop outcomes, and release. Four adversarial raw mutations must all be rejected.

**D.** `PASS_METHOD_SCOPED` requires exactly 30 unique case×arm traces; all safe-arm inputs must match the oracle's final turn/version/principal/intent and explicit authentication/commit booleans; no safe-arm effect on cancel/quotation; no stale or cross-speaker effect; correct pending-unknown and already-occurred typing; verified release before planner completion; lower stable-case logical latency for the version-bound arm; and rejection of all four planted mutations. The naive comparator is expected to produce provisional unsafe inputs in the adversarial cases; the auditor must retain their provisional labels and count them as unsafe, not classify them as valid effects. No speech, human, GUI, model, physical-input, or real-latency result is implied.

**C.** Final-only processing may be sufficiently fast; the assumed preparation overlap may be unrealistic; exact-version gating may discard too much useful preparation; a single schedule does not estimate a distribution. An implementation error in the simulator or auditor can produce internally consistent traces.

**U.** Scripted labels do not establish acoustic recognition, authenticated speaker truth, actual user intent, interruption timing, GUI semantics, irreversibility, or external effect verification. Logical ticks are stipulated costs, not measured durations. This tests method logic only.

## Frozen protocol

- Repository: `Unjuno/agent-interface`; base `main` at `3246a9b6cb7a19209c4056d01472cb660390c4f4`.
- Issue: #6617. No existing branch, open PR, or issue comment allocates this T0; targeted closed-issue search found no same revision-timed cutover simulation.
- Additive branch/path: `research/revision-timed-cutover-6617-t0-wslc-20261002` / `research/analysis/revision_timed_cutover_6617_t0_v1/`.
- Runtime: Microsoft WSL Containers (`wslc.exe`), cached `python:3.12-slim` pinned by image digest; `--pull never`, `--network none`, one CPU requested, source mount read-only, raw/audit outputs written to a separate writable mount. No image build, package install, model, GPU, GUI, voice capture, or user data. WSLc-reported resource limits are requested settings only; enforcement is not assumed.
- Counts: construction tests may run before freeze and are not formal candidate/auditor runs. Formal candidate=1; independent auditor=1; retries=0. Candidate and auditor are separate processes. If either formal invocation fails, preserve it and stop; no retry or relabel.
- Input bytes and all protocol/source hashes are frozen in `FREEZE.json` before the formal candidate starts. The raw first output is immutable and hashed; auditor writes only `formal_01_20261002/audit.json`.
- Failure boundary: malformed/partial raw, source/hash mismatch, container startup failure, nonzero candidate/auditor exit, missed case or mutation acceptance => preserve exact output and classify FAIL/STOP as applicable; do not rerun this allocation.

## Interpretation boundary

Even if every gate passes, this is a deterministic method-scoped synthetic result. It is not evidence for safe speech input, ASR, actual intention, GUI effect, human benefit, or runtime readiness. T1 would require a separate proposal, consent/authority, isolated disposable fixture, independently validated turn/effect truth, a prospective real-time design, and fresh ownership review.
