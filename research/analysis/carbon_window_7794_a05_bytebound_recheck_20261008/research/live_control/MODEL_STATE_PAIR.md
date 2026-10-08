# Text-only interrupted-state presentation comparison

Four fresh CLI turns were registered before model invocation: pending full/composed, terminal composed/full. Sources are actual Calc save results from calc-early-live-01 and calc-combined-live-01, with no screenshots attached. Both arms receive identical decoding instructions and questions, requested Luna/low settings and the same working directory. The composed format is frozen composed_result_v1. The prepared plan pins source, runner, format and exact normalized stdin bytes. model_text_runner_v1 saves binary UTF-8 prompt bytes, addressing the earlier Windows newline hash ambiguity without changing measured older runners.

The requested response has ten fields: lifecycle state, terminal status, completed steps, stop reason, observation sequence, after-sample buttons and keycodes, historical lease-valid flag, input authority and whether task success is proved. Acceptance requires exact JSON values and types. Expected values live in the plan, not in the prompt. Instructions explicitly define null versus zero and historical authority, so this is guided record extraction, not an unprompted safety or planning benchmark.

| Case | Full input | Composed input | Difference | Full/composed cached input | Full/composed output |
|---|---:|---:|---:|---:|---:|
| Input stopped, capture pending | 13199 | 12932 | 267 (2.02%) | 9984 / 1792 | 154 / 145 |
| Terminal needs decision | 14319 | 13828 | 491 (3.43%) | 1792 / 9984 | 125 / 148 |

All four responses match all ten expected fields exactly. Pending terminal and completed steps are null; received terminal is needs_decision with zero completed steps. Both identify focus_changed, empty after-sample owned inputs, no historical valid lease, no input authority and no proof of task success. Sequence numbers 8 and 11 are read correctly. This exercises text/state-table reconstruction beyond visually obvious saved/unsaved images. It still contains only known static records, and empty owned-input arrays are an easy special case.

All four processes exited 0. The independent audit checks source hashes, value reconstruction, identical arguments, binary prompt hashes, raw event hashes and local arrival ordering, usage types and correctness. No tool items were emitted; stderr files were empty. Audit distinguishes evidence validity from answer correctness so a future wrong answer is retained rather than hidden behind a failed assertion. Results are in results/model-state-pair-01.

Cache allocation differs substantially and the output count grows for composed terminal. Do not claim billed savings or speed. Requested model is fixed but served identity and full hidden context equality remain unverified. Total CLI input includes background instructions, not just report tokens. The two input differences are actual reported turn usage, not attribution to any individual field.

Decision: composed representation merits an explicit live-client candidate, but no default promotion. Next test actual use across a changed transition, and include a state mismatch/nonempty input or unresolved error so preserving negative evidence is consequential. Stop repeating these two easy static records to improve a percentage. Full live human-tempo and recovery criteria remain unproved.
