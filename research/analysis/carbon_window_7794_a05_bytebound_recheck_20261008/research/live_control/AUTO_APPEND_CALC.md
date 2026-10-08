# Bounded automatic UTF-8 model handoff on actual Calc

The new Windows auto_append_calc_supervisor_v1 launches the Linux auto_append_calc_driver_v1 and automatically connects current screenshot, model proposal, strict validation, fresh observation, bounded action and next screenshot. No assistant approval/file creation was needed after launch. The task and seed match the prior manual Calc episode: A1=480,A2=192, existing sheet.xlsx in Excel format, requested gpt-5.6-luna/low. The typed prompt and model-proposed action count changed, so this is not a controlled causal speed ratio against the manual episode.

calc_proposal_schema_v1 parses duplicate-free JSON and accepts exactly act/verify/stop variants. Numeric visible cell values must be integers, excluding booleans/strings; dialog state must be boolean. Steps have exact allowed fields, numeric text, bounded1280x800 pointer coordinates and80ms clicks, selected keys/chords and at most10 steps. UTF-8 is explicit at file boundaries and proposals/driver output are atomically renamed. A malformed response stops without model retry. Eight offline type/extra-field/duplicate-key controls refuse; a valid numeric verdict passes. This schema is scoped to the isolated numeric Calc task, not a general desktop action language or semantic target verifier.

Four actual screenshot model calls ran with no manual correction: (1) click A1, enter480/192 and Save; (2) click the observed Excel-format confirmation; (3) request Save again despite the dialog having closed; (4) verify visible values/no dialog and request independent saved-file verification. Both dialog transitions returned needs_decision/focus_changed with input released; the loop used the new screenshot instead of resending the prior transport request. The third proposal is a redundant semantic save with its own new ID, not a transport duplicate. Retain it as inefficiency evidence.

Runtime independent evaluation and separate openpyxl read both confirm saved A1=480,A2=192. XLSX SHA256aaf9d18dc12ac63131a3f791a6e1b938614615464ce4bdc463b6688997f619ec. Six accepted programs (three fresh observations and three model action programs), no rejected programs, two needs_decision terminals and four completed terminals, all verified released. Twelve journal calls plus initial read/finish:14 socket exchanges,25 append frames,86 runtime events,16 exact reconstructed frames. Supervisor/driver exit0, sockets removed, no abort/error artifact. audit_auto_append_calc_v1 validates sources, model prompts/images/output hashes, schema, unchanged proposal-to-action mapping, received continuation/clock/deadline sequence, append state, unique request IDs, explicit two save chords, independent file and cleanup.

## Measured intervals and usage

Supervisor start through verified driver exit39.249s including startup. Linux initial capture through independent evaluation32.570s. Each clock origin is used separately; Windows and Linux timestamps are never subtracted. Model runner walls8.489,5.834,7.428,7.055s, total28.806s. Supervisor model-return to proposal publication14.215,16.247,12.368ms. Linux proposal receipt to action result1.219,0.811,0.611s; source capture to revalidation8.918,6.214,7.837s. This removes the previously observed manual handoff stalls; it still waits seconds per model decision and does not reach human-like live control.

| turn | input tokens | cached input | output tokens |
|---|---:|---:|---:|
|1|12854|1792|181|
|2|13332|9984|114|
|3|13280|9984|108|
|4|13120|9984|84|

Totals52586 input,31744 cached input (subset),487 output. Actual served identity/provider cost/model receipt time remain unavailable. Four calls and changed typed prompts versus the previous three-call manual episode prevent a compression or model-efficiency gain claim. Input includes CLI context, not just task text. No model reruns or malformed responses occurred in this live episode.

The supervisor is bounded to five turns and the driver to its existing proposal/time limits. Fresh focus/binding checks do not prove selected-cell or button semantic identity. No concurrent UI mutation was injected. Unresolved journal responses still raise in the driver rather than enter a production recovery supervisor. Failure cleanup requests finish or terminates its WSL child; that fallback is not a tested full descendant supervisor. Native temporary25-frame append journal behavior is within the short-session regime; growth/compaction/power-loss limits remain. No default promotion.

The next model prompt currently includes only the immediately previous proposal/resolution. After format confirmation this omits the earlier save request, plausibly contributing to the extra save; that is an inference, not established causality. Next compare a bounded factual action/effect history against last-outcome-only context under fixed model/task/environment, retaining token and round-trip measurements. History must remain observed evidence with no task-success or renewed-authority inference. Focus on avoiding unnecessary model/action turns before further checkpoint micro-optimization.
