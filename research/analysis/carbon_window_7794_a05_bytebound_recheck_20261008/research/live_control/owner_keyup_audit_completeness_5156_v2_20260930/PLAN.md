# Owner key-up audit completeness T0 v2

Allocation: `map01-owner-keyup-audit-completeness-5156-t0-v2-20260930-01`
Issue: #5156. Additive successor to Allocation-03; its branch, source and result remain untouched.
Base main: `6b1ad36c0628098c2d1c28b0a1b371db099aecce`
Execution boundary: host-only CPython synthetic construction because #5085 currently forbids Docker/OrbStack calls without a fresh exact assignment. No X11, GUI, physical input, MAP01, model, GPU or CUDA.

## H / T / D / C / U

- **H:** A raw-only auditor bound to a separately frozen expected-release inventory will detect a missing owner key-release bracket, including deletion of every bracket row; validating only rows that happen to remain is insufficient.
- **T:** Freeze a deterministic two-release inventory and runner. Emit two synthetic owner-release rows, then run unit and mutation tests over the independent auditor. The expected inventory is a distinct frozen file, not inferred from the candidate raw output.
- **D:** PASS only if the complete fixture passes and empty/all-row deletion, one-row deletion, duplicate, unexpected identity, malformed event, bool timestamp, inverted order, authority escalation, and physical-key-up claim all fail closed. No release time is promoted as physical or task-useful.
- **C:** Synthetic integrity test only; it neither validates X server timing nor proves release behavior, MAP01 occupancy, task effect, safety, recovery efficacy, GPU utility, or human tempo.
- **U:** A fresh authorized X11 fixture and a plan-bound live MAP01 occupancy/recovery study remain required.

No source/result bytes from #443, #503, #5156 Allocation-03, #5298, or the original v38/v39 runs are changed. This T0 tests audit completeness only.
