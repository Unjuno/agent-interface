# Actual screenshot-model decisions through append caller on Calc

live_append_calc_v1 ran actual isolated Calc seed238 with assistant-reviewed file proposals. Three actual requested gpt-5.6-luna/low screenshot calls used frozen model_pair_runner_v1: initial cell entry/save, format-dialog confirmation, and final visual verdict. This is model-generated action content with assistant review and manual handoff, not an autonomous supervisor. Prompts supplied task values/supported actions and described prior focus outcomes without allowing automatic replay.

The first model proposed entering480 in A1,192 in A2 and Ctrl+S. Journal clock/observe/clock preceded application. The format dialog opened, input was released, and needs_decision/focus_changed suppressed the remaining observe step. The model saw the actual dialog and proposed pointer_click785,463 on Use Excel2007-365 Format. Another fresh clock/observe/clock preceded that exact click. The dialog closed, again returning needs_decision/focus_changed with zero steps_completed despite a visible effect. The third model saw480/192 and no dialog, requesting independent verification instead of replay. The assistant viewed all three input images and accepted the model steps unchanged.

Finish followed that visual verdict. Runtime independent evaluation succeeds; independent openpyxl read confirms saved sheet.xlsx A1=480,A2=192. SHA25617a168dd0ab96af4259dd11baf4e620e2f31f7ab7cc6e4bb0c2e586d4e69ff2a. Four admitted programs: two observations and two model action programs; statuses completed,needs_decision,completed,needs_decision, all released with empty held inputs. No rejected or replayed program. Eight journal requests plus initial/final exchanges;17 append records,63 events,12 exact frames. Driver/bridge exit0, sockets removed. audit_live_append_calc_v1 checks pinned sources, model prompts/images/raw-line hashes/usage, exact proposal-to-program steps, clock/deadline/sequence associations, continuation replay, append state, frames and saved file. Results: results/live-append-calc-01.

| model turn | purpose | input tokens | cached input | output tokens | runner wall seconds |
|---|---|---:|---:|---:|---:|
|1|enter/save|12701|9984|172|8.622|
|2|confirm format|12659|1792|90|5.796|
|3|visual verdict|12611|1792|109|8.145|

Totals37971 input,13568 cached input (subset),371 output; runner wall22.563s. Usage and Windows runner intervals are observed; actual served identity/provider cost/model receipt timestamps remain unavailable. Not a compression comparison; input includes CLI context beyond the task prompt.

Linux-only intervals: source observation to fresh capture55.585s/70.766s; proposal file receipt to result1.101s/0.817s; four API calls per proposal1.046s/0.755s. Initial capture to independent evaluation205.516s includes review, model waits, file handoffs and corrections. Windows/Linux timestamp origins were not subtracted. This manual loop is far from human-like tempo; no matched model/caller baseline or end-to-end speedup claim.

The second-output parsing first failed because Windows default cp932 could not decode UTF-8 punctuation; explicit UTF-8 fixed it before proposal creation. The visual-verdict check initially expected numbers although the prompt did not specify types; exact accurate strings were accepted after review. Neither correction caused a model rerun or extra GUI input. These are harness/schema problems, not model task failure. Notes are retained. Documentation writing also needed explicit UTF-8 after a cp932 failure; no measured source changed.

Fresh observation checks focus/binding, not pixel equality, selected-cell semantics or target identity. There was no concurrent mutation fixture; semantic revalidation under external change remains unproven. Driver waits for assistant files up to300s and expects synchronous resolution, with no automatic pending-read supervisor. Failure cleanup terminates its bridge and is not production supervision. Native temporary journal use retains short-session256-record/no-power-loss limits. No default promotion.

Next automate screenshot-to-typed-UTF-8-proposal-to-validation-to-fresh-observation-to-bounded-action handoff on an isolated task with explicit stop/replan outcomes and full evidence. Remove manual file/schema corrections before more storage micro-optimizations. Measure complete loop/model tokens under fixed conditions; do not treat needs_decision or zero steps_completed as proof an application effect failed. Keep independent saved-result verification.
