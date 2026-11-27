# R45 OS-pipe recovery attempt

Classification: `FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED`; scoped cancellation recovery was later confirmed. R41–R44 first outcomes remain immutable.

## Question and runner change

Can the standard public stdio relay route cancellation and bounded Win32 release while its actual child-process stdout OS pipe is full and a write remains blocked? R45 preserves R44's paired owner/producer roots and R43's public cancel/result/close reconciliation. It extends the action lease to 45 seconds and the SHIFT-down observation window to 12 seconds because R44 reached an authorized producer but canceled before an independent down sample. The observed key state remains a hard gate; timeout cancels and retains exact-call evidence without replay.

## First outcome

Fresh fixture, foreground, target-generation and public observation preflight passed. `interface_dispatch` returned queued. No independent SHIFT-down was observed in 12 seconds, so pipe pressure was not applied. The failure path sent standard `interface_cancel`; the first response was pending. Exact-call results progressed from action `running`/cancellation `pending` to action `recovered`/cancellation `recovered`, with `release_confirmed=true`, producer exit `-15`, and cleanup latency 47 ms from cancellation request. Same-generation native readback found SHIFT up. `interface_close` returned closed with zero unresolved calls; fixture exit was 0 and original foreground HWND was restored exactly. Task success remains null.

This is a scoped public cancellation/recovery sample, not blocked OS-pipe recovery: the down state was not observed and the full-pipe/outstanding-write gate was not reached. Pretrial and raw manifests verify 12/12 and 19/19 entries with no mismatches. No WSLc/Docker operation occurred; no replay. The MCP server adapter is in-process; the relay child stdout is an actual OS pipe. This does not establish production MCP subprocess behavior, MAP01, task effect, matched efficiency, or reliability.
