# Bounded history did not reduce turns in matched Calc ABBA

A predeclared four-episode experiment compared last-outcome-only with all previous proposal/outcome records. history_calc_supervisor_v1 and history_calc_driver_v1 use the same source and flags, isolated Calc seed238, requested gpt-5.6-luna/low, typed schema, screenshots, fresh observation/clock checks, append caller and independent XLSX scoring. Order:last/all/all/last. Both contexts use the same historical-evidence list syntax; the only mode branch chooses history[-1:] versus history. The initial prompt bytes are identical across all four episodes. At most five model turns bound the list; no semantic summarization or new task authority is inferred from history.

All four episodes completed without a retry or selected rerun, each with three model calls, two action proposals and one final verification, one save chord and independent A1=480,A2=192. This failed to reproduce the earlier fourth model call/redundant save even in the last-only condition. Thus omission of earlier history is not established as the cause of that earlier save, and adding history has no demonstrated turn-reduction benefit here.

| episode | context | model calls | saves | input tokens | cached input | output tokens | capture-to-evaluation s |
|---|---|---:|---:|---:|---:|---:|---:|
|1|last|3|1|39433|13568|380|23.646|
|2|all|3|1|39939|19968|436|25.004|
|3|all|3|1|39870|13568|338|24.640|
|4|last|3|1|39444|3584|395|22.470|

Mean input39438.5 last versus39904.5 all, an increase466 tokens per completed task for all-history. Mean capture-to-evaluation23.058s versus24.822s; observed model-runner means20.441s versus22.101s. These are descriptive small-sample values, not causal latency estimates: model sampling/served identity are not controlled, cached context varies, and first-action choices differ before history can affect them. Independent trials are two per mode, not twelve independent treatment samples. Startup is excluded from Linux capture intervals; full Windows supervisor times are also retained in per-episode audits. Clocks are not mixed. Model costs and provider receipt times remain unavailable.

Per-episode audit_history_calc_v1 checks pinned sources, exact context lists against previous received proposals/outcomes, image/prompt hashes, raw model line hashes, exact parsed-proposal-to-GUI mapping, unique request IDs, full event/continuation replay, deadlines, released terminals, frame reconstruction, append state and independent workbook/cleanup. Totals244 events,48 exact image frames,68 journal records and40 socket exchanges across four sessions. Three have60 events, one64 due to different model-selected input steps. All supervisor/driver exits0, sockets removed, no abort/error artifacts. run_history_abba_v1 freezes order and source hashes before launch; results/history-abba-01 contains plan,runs,all process logs and summary; individual results/history-abba-{1-last,2-all,3-all,4-last} contain full evidence.

Decision: do not promote all-history as the default or claim compression/turn savings. Keep last-outcome context and archived full history available for later targeted uses. This negative result is useful because it prevents additional context cost based on one anecdotal repeated save. The finding is only for a short three-decision Calc task; long-horizon or multi-object tasks may need history and were not tested. Focus/binding checks still do not prove semantic target identity under external mutations, and the supervisor/storage bounds remain unchanged.

Next isolate which received fields need to be presented every model turn and which can remain retrievable evidence. Evaluate a bounded presentation candidate on fixed actual tasks, retaining unknown fields/refusals and measuring tokens, independent success and loop waiting. Avoid further identical history trials just to seek a favorable outcome. Domain coverage/human-tempo and general-interface goals remain active.

GitHub Issue list was also checked during this run; #40-51 updated timestamps were unchanged (2026-09-13T01:13-01:19Z). No Issue was posted, edited or closed.
