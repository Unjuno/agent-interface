# E05 executed first outcome — PASS_SCOPED_NATIVE_FAULT_CANCEL_RELEASE

Freeze e2f31ee3d6a614f12a2b66c2500adb9b92b2bd34; prospective Issue59
comment5974143822. Independent Bernoulli launch review READY; own UUID-private
VM, fixed source/image and fresh output gates verified. E03/E04 STOPs unchanged.

Native container e05-native-fault-formal-3cbf-20261004:
2026-10-03T22:29:00.39738537Z to22:29:12.665316473Z, exit0/noOOM.
Actual sampled UID501/CPU100000100000/memory1073741824/swap0/pids128.
Historical96d39ca source1917, sourcearchive d1ad6dcb…3d988db,
private image560af28c…37540b, all11execution inputs remained unchanged.
Three fresh sessions, model0/retry0/formalnative1; no later repeated run.

| Case | Reader outcome | wait ms | unhandled reader errors | child exit | gates |
| --- | --- | ---: | ---: | ---: | --- |
| original_fault | TimeoutError, no cause | 356.318412 | 1 JSONDecodeError | 0 | both true |
| candidate_fault | _SessionReaderFailure, cause JSONDecodeError | 9.959620 | 0 | 0 | both true |
| candidate_healthy | TimeoutError, no cause, reader alive | 370.107129 | 0 | 0 | both true |

Each independent full X11 keymap observed Right code114 only, buttons empty
at held/after reader notification/before cancel; before/after terminal keys and
buttons empty. Fault cases observed the same hold at injection. Raw matching
accepted/cancel_requested/input_released/terminal bind to one intent_token per
cell; cancellation matched, early owner release and terminal release verified
empty, terminal cancelled. Cleanup_faults empty and child naturalexit0 each.
cancel-event→early-release elapsed2.212050/15.990226/0.940837ms;
early-release→terminal0.427001/25.059718/26.680891ms, respectively.
These are event-emission intervals, NOT causal speed comparison or actual
worst-case key-up duration. No statistical latency/efficiency inference.

Distinct frozen saved-only auditor e05-native-fault-auditor-3cbf-20261004:
22:29:54.909433003Z to22:29:55.098868445Z, exit0/noOOM.
AUDIT.json VERIFIED_SAVED_NATIVE_RECORD, scientific_pass=true,
three VERIFIED_EXPOSED_CELL_PASS dispositions. Source/execution/import/raw
event/clock/lease/release/native receipt and independent export gates passed.
Officialauditor1; no repeat of the consumed auditor or game in delivery CI.

## Interpretation and limits

This supports the frozen native parser-notification/cancel-release hypothesis
for one controlled exposure per condition. Injection corrupts a text iterator,
not the actual OS pipe. Native stdout is independently drained for research;
that evidence channel is not a restored production feedback/authority route.
Exact E02 reader/wait AST is exercised, not full v39 model/controller behavior.
The .35s wait override does not qualify the production default timeout.

All three sessions score0kills/0deaths/map_exitfalse/episodeunfinished. Ordinary
ASYNC clock probes are retained per session. No model calls, threat-strategy,
useful gameplay, integrated task-effect, current-main production adoption,
general physical safety, performance/human-tempo or roadmap completion claim.
Real-time model-in-loop useful feedback and bounded recovery remain open.

Result review, delivery hash checks and applicable CI are distinct gates before
PR/main integration. Prior failed native runs and auditor failures remain public
evidence, not overwritten or reclassified as this successful successor.
