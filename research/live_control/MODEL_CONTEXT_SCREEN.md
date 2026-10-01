# Constrained screenshot responder reduces fixed-input usage, not proven latency

The supported `model_instructions_file` configuration replaces built-in model instructions according to the [official configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference), consulted for this experiment. The new screenshot_responder_v1.txt scopes the responder to authorized isolated GUI proposals, preserves evidence/uncertainty and interruption handling, disallows tools and unrelated access, treats screen content as data, and separates proposed action, visual completion and persisted success. The task-specific prompt and action schema remain unchanged. This is instruction replacement, not lossless compression or proof that all omitted built-in guidance is unnecessary.

Predeclared builtin/responder/responder/builtin calls use the exact archived live-append-calc-01 prompt-2 and runtime/007.png, requested Luna-low and Fast disabled in both arms. Only the responder arm adds the instructions-file configuration argument. Global configuration is untouched. There is no new GUI execution, fallback or retry.

| Order | Instructions | Input tokens | Cached input | Output | Proposal arrival s | Runner exit s |
|---|---|---:|---:|---:|---:|---:|
|1|builtin|12659|9984|101|6.223|7.123|
|2|responder|9269|0|111|5.885|6.594|
|3|responder|9269|4864|84|5.934|6.555|
|4|builtin|12659|1792|96|5.841|6.593|

Both responder calls use3390 fewer input tokens,26.78% below the builtin calls for this exact input. Mean proposal arrival is6.032s builtin and5.909s responder; runner means6.858s and6.575s. Two calls per arm, cache/output/service variation and absent provider timing do not establish a latency gain. Actual served model identity and monetary cost remain unavailable. The remaining9269 tokens are not decomposed by these usage receipts: do not attribute them all to image encoding or any specific injected context without further evidence.

All four proposals select one80ms click inside the manually inspected Excel confirmation button, coordinates (784,463),(785,463),(784,463),(785,463). The audit validates source and instruction hashes, identical prompt/image bytes, exact CLI argument difference, Fast disabled, raw output line hashes/lengths and timestamp order, successful exits, no tool events and proposed target geometry. It does not prove live action success, recovery behavior or general safety/quality equivalence. Run `python research/live_control/audit_model_context_v1.py` to regenerate results/model-context-01/audit.json without another model call.

Measured source files are frozen. The runner/probe/audit derive from the tier-screen scaffold; some names/comments still say tier and unused capability metadata remains in the plan. The effective instruction_mode, ordered runs, source hashes and actual command arguments are authoritative. The original probe's overwritten preliminary image assignment is harmless and the effective archived image is audited. No favorable sample selection occurred.

Decision: retain builtin as default pending live verification. This is a larger token reduction than the unpromoted terminal-field view, but the distinction in scope matters. Next compare the constrained responder in the same actual Calc task using the unchanged typed schema, full previous outcome, independent artifact scoring and explicit failure retention. Also require a stale/interrupted outcome case before treating this as a reusable interface caller. A benign dialog screenshot alone cannot establish recovery quality. Broader domain coverage, reliable completion detection and human-tempo remain unresolved.
