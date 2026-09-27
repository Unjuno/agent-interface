# Fixed screenshot tier screening: promising request setting, not a verified speedup

The four predeclared default/fast/fast/default calls in results/model-tier-01 use the exact archived live-append-calc-01 prompt-2 and runtime/007.png. Requested model is gpt-5.6-luna with low reasoning throughout. The only CLI argument difference is disabling fast_mode versus enabling fast_mode and requesting service_tier="fast". User configuration is ignored; global settings are unchanged. There are no new GUI inputs, retries, or automatic fallback. This measures local CLI start to response arrival/exit, not provider inference time or live task completion.

| Order | Requested mode | Proposal arrival s | Runner exit s | Input | Cached input | Output |
|---|---|---:|---:|---:|---:|---:|
|1|default|6.162|6.809|12659|9984|120|
|2|fast|4.636|5.237|12659|0|105|
|3|fast|5.559|6.219|12659|0|98|
|4|default|7.543|8.153|12659|0|92|

Mean proposal arrival is 6.852s default and 5.098s fast-requested; mean runner duration is 7.481s and 5.728s. These are descriptive values from two calls per condition. Cache state, generated output length and transient service behavior vary. No population estimate, causal speedup, human-tempo claim, or interface improvement follows. CLI acceptance does not prove the provider honored the requested tier: observed tier, serving identity, provider receipt timing and monetary cost remain unavailable.

All four responses contain one pointer click inside the manually inspected Excel-format confirmation button. The screenshot visibly contains A1=480 and A2=192. The proposed coordinates are (785,463), (784,463), (783,463), (785,463). This is a fixed-image proposal correctness check, not independent saved-artifact success from new execution. The audit replays source hashes, identical prompt/image, exact argument difference, raw JSONL line hashes and lengths, arrival ordering, no tool events, successful exits, and proposal geometry. Run `python research/live_control/audit_model_tier_v1.py` to regenerate audit.json without model or GUI calls.

The local capability catalog snapshot (fetched 2026-09-13T13:22:36.976490300Z, client 0.154.0) lists text/image input and a Fast tier for Luna. It lists only text for Spark, so Spark was not attempted in this direct screenshot comparison. That is an environment-specific eligibility decision, not a universal statement about Spark. Selected metadata is retained in plan.json. The measured runner and probe source bytes are frozen; the probe has an unused initial image assignment that is overwritten before use. Both effective image hashes and CLI paths are audited.

The [official speed configuration documentation](https://learn.chatgpt.com/docs/agent-configuration/speed), consulted when configuring this probe, describes Fast as trading greater usage for speed. Its advertised multipliers are not measurements of this experiment. No account reset, credit purchase, or persistent speed-setting change was performed.

Decision: retain default settings. This result warrants a bounded matched live-loop comparison, using the same full previous-outcome prompt, schema, task seed and runtime in both arms. Measure independent saved artifact correctness, model turns, repeated saves, capture-to-evaluation time, model-arrival intervals and usage, retaining failures. Report any effect as a model-call setting result separately from interface changes. If actual tier remains unobservable, label the comparison by requested mode. Do not repeat fixed screenshots until a favorable result or promote Fast from these four samples. Broader domain coverage and human-like live operation remain open requirements.
