# H/T/D/C/U — #57 desktop handoff reconstruction A01

**H — Hypothesis.** In the retained Calc episode, capture-time window context and focus agreement are not enough to determine whether a modal dialog is visually ready for a guarded decision; an additional observation may deliver the first visibly painted dialog frame.

**T — Treatment.** Posthoc analysis only: select sequences 6–9 from `recovery-assistant-01`, verify timestamps/focus flags and image hashes, then compare decoded PNG pixels and image-ready timestamp deltas.

**D — Design / strongest comparison.** The strongest available comparison is within-episode adjacency: #006→#007 brackets the unpainted-to-painted dialog transition; #007→#008 follows the Return action; #008→#009 follows an explicit observe-only recovery. It is not randomized or matched, and intervals include unspecified application, orchestration, planner, and tool time.

**C — Criterion.** Reconstruction passes if source event identities and hashes validate, the existing audit confirms its nine-frame/four-program task and release record, and independent image comparisons reproduce the transition magnitudes. A pass validates the reconstruction only.

**U — Update / uncertainty.** The reconstruction confirms a large visual change #006→#007, a small change #007→#008 while the dialog remains visible and focus samples differ, and another large change #008→#009 to the worksheet. It supports a bounded handoff question, not useful-feedback onset, causal timing improvement, general modal reliability, a new sensor, or any default wait policy. Next useful experiment needs an authorized fresh allocation with prespecified useful-feedback criteria and matched timing; this record does not authorize that run.

## Current primary-caller composition check

`test_replay.mjs` serves these retained images through a deterministic temporary MCP child and exercises the existing `runtime/host_v1` relay and `createPrimaryCaller`: one initial input, explicit observe after #006, one confirmation input, explicit observe after stale #008. The capped replay allows exactly two explicit observations; a third helper call is refused locally before a fifth host request and latches STOP. Both raw requests, replies, event journals, reviews and exit records are retained and SHA-pinned; `audit_replay.py` independently verifies image/source/release joins and the refused extra observation, separately carrying forward the original independent task score. The count cap is caller-selected, measured over one caller's lifetime, and does not bound wall time or detect useful pixels. This verifies only that the selected current host path can carry a bounded handoff without automatic replay; it is not a GUI run or proof that an agent will interpret images correctly.

## Identity and provenance

- Parent question: Issue #57 desktop observation/decision handoff.
- Input package: `research/live_control/results/recovery-assistant-01/`; raw inputs are SHA-256 pinned in `SHA256SUMS`.
- Type: posthoc single-trajectory reconstruction; no live allocation consumed.
- `analyze.py` is the reproducer; `RESULT.json` is generated output; `SHA256SUMS` pins all directly-read source artifacts and the analysis, replay and audit scripts. `REPLAY_SHA256SUMS` pins the retained relay output.
