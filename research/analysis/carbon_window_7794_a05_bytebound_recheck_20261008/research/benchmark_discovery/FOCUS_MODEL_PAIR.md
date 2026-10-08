# Focus decision projection: real model pair fails acceptance

Four actual Codex CLI model invocations used the existing explicit model_text_runner_v1, requested gpt-5.6-luna/low, identical CLI arguments and working directory, no tools, no images. Before invocation, prepare_focus_model_pair_v1 froze prompts, source hashes, order and expected JSON for two recorded states from actual Mindustry recovery. Order: lost-full, lost-view, restored-view, restored-full. Every invocation exited0, returned one message, had empty stderr and no tool items. Raw stdout events, per-line local arrivals, prompt bytes and usage remain available in results/focus-model-pair-01.

focus_decision_view_v1 selects a single terminal and latest matching observation, retaining release, pointer binding, focus and after-input-state evidence. It adds an explicit no-authority cue and omits earlier observations/admissions. This is a deliberately lossy, narrow experimental view, not a drop-in lossless receipt or a validated general parser. Full original replies remain authoritative. The authority cue is an additional difference between arms; this experiment cannot isolate compression from wording effects.

| Arm | Input tokens | Cached input tokens | Output tokens | Predeclared rubric |
|---|---:|---:|---:|---|
| Lost, full |12574|1792|212|Mismatch: replay_interrupted_tail true|
| Lost, view |11705|9984|165|All eight fields match|
| Restored, view |11727|1792|161|Mismatch: chooses restore_focus_then_reobserve|
| Restored, full |13557|9984|153|Both replay and next-step mismatch|

The view reduced reported input tokens by869 (6.91%) for lost focus and1830 (13.50%) for restored focus, but only one of four outputs matched the entire rubric. Therefore the candidate fails the declared all-fields acceptance gate. No reruns were made to improve answers. All outputs correctly reported needs_decision/focus_changed, the latest sequence, whether the target pointer binding was observed, no old-lease reuse and no game-task proof. Both restored-case outputs recognized the target binding while selecting another restoration step.

Interpretation limits matter. The expected next-step labels encode a policy preference and do not fully specify what to do when historically observed focus is stale; choosing another restoration may be conservative rather than factually wrong. Likewise replay_interrupted_tail lacks an explicit automatic-versus-new-intent distinction in the question, although the intended rubric prohibits replay and requires fresh admission. Treat these as rubric mismatches, not proof of malicious behavior or an unconditional unsafe-model claim. The prompts also supply an explicit authority cue only in the projected payload. Improve the decision schema before inferring comparative reasoning ability.

Local runner durations were9.867,7.271,7.466,6.644 seconds in order. Cache amounts/order differ, no repeated cohort exists, and actual served identity/full context are not independently verified. These are local CLI durations, not model receipt timestamps, live recovery latency or causal speed gains. Cost remains unmeasured; token reductions do not establish lower bills. audit_focus_model_pair_v1 validates source/prompt hashes, identical arguments, raw event arrival hashes, no-tool single messages and every mismatch without treating a passing integrity audit as successful model acceptance.

Next define unambiguous separate outputs for historical target observation, unconditional prohibition of automatic tail replay, need for fresh validation, and an explicit new action proposal. Keep runtime checks authoritative. Compare equivalent cues in both arms on new cases, including target already restored, stale observation and unknown binding. Do not promote this lossy view based on token savings, and do not repeat the same four prompts to chase a passing result.
