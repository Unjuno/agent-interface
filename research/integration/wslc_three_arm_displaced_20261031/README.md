# WSLc Chromium: displaced-form three-arm experiment

The earlier seed changed only the text token, leaving both form layouts fixed. This prospectively frozen research variant moves the entire A form from CSS margin (top 180, left 55) to (120, 225) pixels, and the B form from (330, 430) to (260, 650). The cold/warm A sequence and invalidation/repair B sequence remain the same. Apart from these two CSS substitutions, the 2,092 mounted source files match the preceding current-main snapshot; seed 991037 changes the submitted tokens. This is an experimental fixture fork, not an assertion that the source is identical to main.

The fixed order was ephemeral → persistent → plain, each in a fresh isolated WSLc container and model session, on `gpt-6.1-sol` low. All arms produced six independently exact submissions, and all 123 recorded terminal events had verified empty keys and buttons.

| Arm | Measured lifecycle | Calls: preflight + tasks | Input tokens (cached subset) | Output tokens | Exact tasks | Neutral terminals |
|---|---:|---:|---:|---:|---:|---:|
| ephemeral | 52.748 s | 1 + 6 | 105,365 (58,752) | 851 | 6/6 | 48 |
| persistent | 36.946 s | 1 + 2 | 36,841 (20,608) | 390 | 6/6 | 57 |
| plain | 39.238 s | 1 + 6 | 103,955 (73,728) | 478 | 6/6 | 18 |

The first field grounding moved from approximately (235, 402) in the preceding fixture to approximately (405, 342) in this variant for the compiled arms, consistent with the recorded displacement; screenshot/call records are retained. Within this one block, persistent used 64.56% fewer recorded input tokens and had a 5.84% shorter measured lifecycle than plain. Cached tokens are included in input and not added again; price is unknown. Timing includes preflight, host/container/app startup, tasks, scoring, cleanup and polling, but excludes source preparation, launcher initialization, image build and postrun audit.

This is one fixed-order sample of one small synthetic layout change. The layout, token seed and execution order differ from earlier blocks, so their timing differences cannot be attributed to any one change. The model still sees the displaced target during grounding, and all tasks use the same two reviewed layout families; this is not a hidden or broad visual benchmark, second application, general speed/reliability result or MAP01 completion. Differing arm tool behavior and provider/load/cache effects remain. Issue 57 remains open.

`public.zip` retains scripts, frozen conditions, schemas, usage/call records, screenshots, submission histories, terminal releases, timers, cleanup and source hashes. The baseline and altered fixture source are included; the audit checks that the **only** source change is the two specified CSS substitutions and matches the prior packet's fixture hash. Six private host journals are separately hash-indexed. Remaining source and image bytes are not included; host/provider dependencies are not fully frozen. `python audit.py` verifies the packet, task and release records, source verification summary, and named-container cleanup.
