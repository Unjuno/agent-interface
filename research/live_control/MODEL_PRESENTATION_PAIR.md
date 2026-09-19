# First actual token comparison of full and shared result presentations

Four fresh CLI turns were registered before execution: unsaved full/shared, then saved shared/full. All requested gpt-5.6-luna with low reasoning using model_pair_runner_v1, identical CLI arguments except image, the same working directory, and identical instructions. Each within-scene pair attached the same PNG. Inputs were the previously recorded browser confirmation results; shared_result_v1 was unchanged and reconstructs all original JSON values. Preparation pins source, image and normalized prompt hashes. This is two known static scenes, not live GUI control or held-out task generalization.

| Scene | Full input | Shared input | Difference | Full/shared cached input | Full/shared output |
|---|---:|---:|---:|---:|---:|
| Unsaved warning | 15508 | 15373 | 135 (0.871%) | 0 / 1792 | 88 / 82 |
| Submission received | 15139 | 15008 | 131 (0.865%) | 1792 / 1792 | 73 / 85 |

All four answers correctly distinguish saved/unsaved and say program completion does not prove task success. Both unsaved answers propose checking confirmation and saving. Instructions explicitly caution about semantic completion, and the pictures alone make these easy decisions; this does not establish reasoning over the complete shared structure. No defaults change. The actual turn-input difference is under one percent on these cases, insufficient to justify reference resolution complexity or claim a general cost win. Cache behavior differed; no price calculation or causal latency claim is made.

The independent audit checks registered source hashes, exact value reconstruction, prompt/image consistency, common CLI arguments, four raw events per run, every event hash and ordered local arrival time, exit 0, answers and usage types. There were no emitted tool items or MCP diagnostics. Actual served model identity, hidden context equality and authoritative model timestamps remain unverified. Local elapsed values remain in raw evidence rather than a speed headline.

A preliminary debug prompt-input inventory returned three messages: developer 10030 bytes, context user 876 bytes and diagnostic user 309 bytes under default json.dumps serialization. Text was neither printed nor persisted. That command lacks exec's ignore-user-config flag, so its inventory is not proof of the actual model inputs and is not a token estimate.

Audit v1 failed because it compared planned LF UTF-8 hashes with Windows text-file CRLF hashes. This was an audit assumption error. Runner read_text normalized the text before UTF-8 stdin writing. Audit v2 separately verifies raw saved file equality and the normalized intended-stdin hash. The failed auditor and failure note remain; no model reruns were performed. Actual stdin receiver bytes were not independently captured. Future runner versions should save binary stdin payloads explicitly, but frozen measured sources are unchanged.

Results: results/model-presentation-pair-01. Next stop tuning exact object sharing on these familiar cases. A useful next presentation candidate should remove unnecessary duplicated composition while preserving source references and negative diagnostics, and should be evaluated on less visually obvious evidence or actual operation/recovery, with a fixed preregistered comparison. Overall human-like live control, independent model timing and billed cost remain unfinished.
